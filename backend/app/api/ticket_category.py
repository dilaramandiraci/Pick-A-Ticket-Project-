from fastapi import APIRouter
from app.database.session import cursor, conn
from app.models.ticket_category import TicketCategory
from fastapi import HTTPException
from uuid import UUID
from typing import List
router = APIRouter()

@router.get("/{event_id}", response_model=List[TicketCategory])
async def get_all_ticket_categories_for_event(event_id: UUID):
    query = """
    SELECT * FROM Ticket_Category WHERE event_id = %s;
    """
    cursor.execute(query, (str(event_id),))
    ticket_categories = cursor.fetchall()

    new_ticket_categories = []
    for category in ticket_categories:
        new_ticket_categories.append(TicketCategory(**{
            'event_id': category[0],
            'category_name': category[1],
            'price': category[2],
            'start_column': category[3],
            'end_column': category[4],
            'start_row': category[5],
            'end_row': category[6]
        }))

    if not ticket_categories:
        raise HTTPException(status_code=404, detail="No ticket categories found for this event")
    return new_ticket_categories


@router.get("/{event_id}/{category_name}", response_model=TicketCategory)
async def read_ticket_category(event_id: UUID, category_name: str):
    query = """
    SELECT * FROM Ticket_Category WHERE event_id = %s AND category_name = %s;
    """
    cursor.execute(query, (str(event_id), category_name))
    ticket_category = cursor.fetchone()
    if not ticket_category:
        raise HTTPException(status_code=404, detail="Ticket category not found")
    ticket_category = {
        "event_id": ticket_category[0],
        "category_name": ticket_category[1],
        "price": ticket_category[2],
        "start_column": ticket_category[3],
        "end_column": ticket_category[4],
        "start_row": ticket_category[5],
        "end_row": ticket_category[6]
    }
    return ticket_category



@router.post("", status_code=201)
async def create_ticket_category(ticket_category: TicketCategory):
    ticket_category_query = """
    INSERT INTO Ticket_Category (event_id, category_name, price)
    VALUES (%s, %s, %s)
    RETURNING *;
    """
    seating_plan_query = """
    INSERT INTO Seating_Plan (event_id, category_name, row_number, column_number, is_available)
    VALUES (%s, %s, %s, %s, TRUE);
    """
    try:
        # Create the ticket category
        cursor.execute(ticket_category_query, (str(ticket_category.event_id), ticket_category.category_name, ticket_category.price))
        new_ticket_category = cursor.fetchone()
        
        # Generate seating plan entries
        for row in range(ticket_category.start_row, ticket_category.end_row + 1):
            for col in range(ticket_category.start_column, ticket_category.end_column + 1):
                cursor.execute(seating_plan_query, (str(ticket_category.event_id), ticket_category.category_name, row, col))
        
        conn.commit()  # Commit all changes
        
        return TicketCategory.parse_obj({
            "event_id": new_ticket_category[0],
            "category_name": new_ticket_category[1],
            "price": new_ticket_category[2],
            "start_column": ticket_category.start_column,
            "end_column": ticket_category.end_column,
            "start_row": ticket_category.start_row,
            "end_row": ticket_category.end_row
        })
    except Exception as e:
        conn.rollback()  # Rollback in case of any error
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{event_id}/{category_name}", response_model=TicketCategory)
async def update_ticket_category(event_id: UUID, category_name: str, ticket_category: TicketCategory):
    query = """
    UPDATE Ticket_Category SET price = %s WHERE event_id = %s AND category_name = %s RETURNING *;
    """
    try:
        cursor.execute(query, (ticket_category.price, str(event_id), category_name))
        updated_ticket_category = cursor.fetchone()
        conn.commit()
        if not updated_ticket_category:
            raise HTTPException(status_code=404, detail="Ticket category not found")
        return TicketCategory(**updated_ticket_category)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}/{category_name}", status_code=204)
async def delete_ticket_category(event_id: UUID, category_name: str):
    query = """
    DELETE FROM Ticket_Category WHERE event_id = %s AND category_name = %s RETURNING *;
    """
    cursor.execute(query, (str(event_id), category_name))
    deleted_ticket_category = cursor.fetchone()
    conn.commit()
    if not deleted_ticket_category:
        raise HTTPException(status_code=404, detail="Ticket category not found")
    return {"detail": "Ticket category deleted successfully"}