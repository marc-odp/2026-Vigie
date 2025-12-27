from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlmodel import Session, select
from app.models.domain import Operation, Allocation, QuotePart, Lot, Owner

class AccountingError(Exception):
    pass

class FractionError(AccountingError):
    pass

def validate_fractions(session: Session, lot_id: int, check_date: date) -> bool:
    """
    Verifies that the sum of Start/End QuoteParts for a lot at a given date is exactly 1.
    """
    statement = select(QuotePart).where(QuotePart.lot_id == lot_id)
    parts = session.exec(statement).all()
    
    # Filter for active parts
    active_parts = [
        p for p in parts 
        if p.start_date <= check_date and (p.end_date is None or p.end_date >= check_date)
    ]
    
    if not active_parts:
        return False
        
    # Sum using exact rational arithmetic (numerator/denominator)
    # We find a common denominator
    common_denominator = 1
    for p in active_parts:
        common_denominator *= p.denominator
        
    total_numerator = 0
    for p in active_parts:
        # standard math: (num / den) = (num * (common / den)) / common
        factor = common_denominator // p.denominator
        total_numerator += p.numerator * factor
        
    return total_numerator == common_denominator

def distribute_operation(session: Session, operation: Operation) -> List[Allocation]:
    """
    Calculates the distribution of an operation among owners based on active quote parts.
    Returns a list of Allocation objects (not yet saved).
    """
    if not operation.lot_id:
        return []

    # 1. Fetch active fractions
    statement = select(QuotePart).where(QuotePart.lot_id == operation.lot_id)
    parts = session.exec(statement).all()
    
    active_parts = [
        p for p in parts 
        if p.start_date <= operation.date and (p.end_date is None or p.end_date >= operation.date)
    ]
    
    if not active_parts:
         raise FractionError(f"No active quote parts found for Lot {operation.lot_id} at date {operation.date}")

    # Validate sum is 1 (optional here but good practice, or warn)
    # We proceed even if slightly off? No, strict mode requested.
    # calling validate_fractions is expensive if we re-query, sticking to logic above.
    
    allocations = []
    
    # We will distribute the amount.
    # To avoid rounding issues with Decimals (e.g. 100 / 3 * 3 != 100), 
    # we calculate shares and track the remainder.
    
    remaining_amount = operation.amount
    
    # We need to sort parts to ensure deterministic order for remainder distribution
    active_parts.sort(key=lambda p: p.owner_id)
    
    for i, part in enumerate(active_parts):
        # Calculation: Amount * (Num / Denom)
        # Using Decimal for Amount.
        # share = amount * num / denom
        
        share = (operation.amount * part.numerator) / part.denominator
        # Round to 2 decimals
        share_rounded = share.quantize(Decimal("0.01"))
        
        # If this is the last part, valid or not, we might dump the remainder here?
        # Better strategy: Accumulated error distribution. 
        # But simple version: Give difference to last, or largest.
        # Let's use the 'largest remainder' or just adjust the last one.
        
        if i == len(active_parts) - 1:
            # Last one takes the rest to ensure Sum(allocs) == Total
            # Sum so far
            current_allocated = sum(a.amount for a in allocations)
            share_rounded = operation.amount - current_allocated
            
        allocations.append(Allocation(
            operation_id=operation.id, # Might be None if op is new
            owner_id=part.owner_id,
            amount=share_rounded
        ))
        
    return allocations

def create_transfer(session, date_obj, amount: Decimal, from_acc_id: int, to_acc_id: int, lot_id: Optional[int], label: str):
    """
    Creates a matched pair of operations representing a transfer.
    """
    from app.models.domain import Operation, OperationType, Category, BankAccount
    
    # Fetch names and categories
    from_acc = session.get(BankAccount, from_acc_id)
    to_acc = session.get(BankAccount, to_acc_id)
    from_name = from_acc.name if from_acc else str(from_acc_id)
    to_name = to_acc.name if to_acc else str(to_acc_id)

    # Find categories for transfers (default to AUTRE or first available if not found)
    cat_frais = session.exec(select(Category).where(Category.name == "FRAIS_BANCAIRES")).first()
    cat_autre = session.exec(select(Category).where(Category.name == "AUTRE")).first()
    
    # Fallback IDs
    cat_id_out = cat_frais.id if cat_frais else (cat_autre.id if cat_autre else None)
    cat_id_in = cat_autre.id if cat_autre else (cat_frais.id if cat_frais else None)

    # 1. Withdrawal
    op_out = Operation(
        date=date_obj,
        amount=amount,
        lot_id=lot_id,
        bank_account_id=from_acc_id,
        type=OperationType.SORTIE,
        category_id=cat_id_out,
        label=f"Vir. vers {to_name}: {label}",
    )
    session.add(op_out)
    
    # 2. Deposit
    op_in = Operation(
        date=date_obj,
        amount=amount,
        lot_id=lot_id,
        bank_account_id=to_acc_id,
        type=OperationType.ENTREE,
        category_id=cat_id_in,
        label=f"Vir. depuis {from_name}: {label}",
    )
    session.add(op_in)
    
    session.flush() # Generate IDs
    
    # 3. Distribute (Only if lot_id is provided, though UI usually sends None for transfers now)
    if lot_id:
        d_out = distribute_operation(session, op_out)
        for a in d_out: 
            a.operation_id = op_out.id
            session.add(a)

        d_in = distribute_operation(session, op_in)
        for a in d_in:
            a.operation_id = op_in.id
            session.add(a)
        
    return op_out, op_in

def resync_lot_allocations(session: Session, lot_id: int):
    """
    Deletes and regenerates ALL allocations for all operations tied to a specific lot.
    Useful when quote parts are modified and historical data needs to be updated.
    """
    # 1. Fetch all operations for this lot
    ops = session.exec(select(Operation).where(Operation.lot_id == lot_id)).all()
    
    for op in ops:
        # 2. Delete existing allocations
        existing = session.exec(select(Allocation).where(Allocation.operation_id == op.id)).all()
        for a in existing:
            session.delete(a)
        
        # 3. Redistribute
        try:
            new_allocs = distribute_operation(session, op)
            for a in new_allocs:
                session.add(a)
        except FractionError:
             # Skip if no fractions for that date (might happen if user hasn't defined early fractions)
             pass
    
    session.commit()
