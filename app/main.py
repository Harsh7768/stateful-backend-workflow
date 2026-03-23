from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from app.db import get_connection
from jose import jwt
from datetime import datetime, timedelta


# Secret key used to sign and verify JWT tokens
SECRET_KEY = "mysecretkey"

# Hashing algorithm used for token signature
ALGORITHM = "HS256"

# Token expiry duration for security
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
security = HTTPBearer()


# Decode and validate JWT token, extract authenticated user
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return int(user_id)

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Request model for creating users
class UserCreate(BaseModel):
    email: str

# Request model for login
class LoginRequest(BaseModel):
    email: str = Field(example="test@example.com")

# Request model for creating workflows
class WorkflowCreate(BaseModel):
    name: str = Field(example="Order Processing Workflow")

# Request model for updating workflow state
class WorkflowStateUpdate(BaseModel):
    state: str



# Simple health endpoint to verify server is running
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Verify database connectivity
@app.get("/db-check")
def db_check():
    conn = get_connection()
    conn.close()
    return {"db": "connected"}



# Create a new user in the database

@app.post("/users")
def create_user(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (email) VALUES (%s) RETURNING id;",
            [user.email]
        )
        user_id = cur.fetchone()[0]
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

    finally:
        cur.close()
        conn.close()

    return {"id": user_id, "email": user.email}


# Login endpoint to generate JWT token
@app.post("/login")
def login(request: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Check if user exists
        cur.execute(
            "SELECT id FROM users WHERE email = %s;",
            (request.email,)
        )
        result = cur.fetchone()

        if not result:
            return {"error": "User not found"}

        user_id = result[0]

        # Create token payload
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "exp": expire
        }

        # Generate JWT token
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    finally:
        cur.close()
        conn.close()

    return {"access_token": token}


# Create a workflow and record its initial state
@app.post("/workflows")
def create_workflow(
   workflow: WorkflowCreate,
    current_user_id: int = Depends(verify_token)
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Insert workflow with initial state
        cur.execute(
            """
            INSERT INTO workflows (user_id, name, current_state)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (current_user_id, workflow.name, "created")
        )

        workflow_id = cur.fetchone()[0]

        # Record state history
        cur.execute(
            """
            INSERT INTO workflow_states (workflow_id, state)
            VALUES (%s, %s);
            """,
            (workflow_id, "created")
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

    return {
        "workflow_id": workflow_id,
        "state": "created"
    }



# Update workflow state with validation
@app.put("/workflows/{workflow_id}/state")
def update_workflow_state(
    workflow_id: int,
    update: WorkflowStateUpdate,
    current_user_id: int = Depends(verify_token)
):
    conn = get_connection()
    cur = conn.cursor()

    # Define valid state transitions to enforce workflow rules
    allowed_transitions = {
        "created": ["in_progress"],
        "in_progress": ["completed"],
        "completed": []
    }

    try:
        # Get current state
        cur.execute(
            "SELECT current_state FROM workflows WHERE id = %s;",
            (workflow_id,)
        )
        result = cur.fetchone()

        if not result:
            return {"error": "Workflow not found"}

        current_state = result[0]
        new_state = update.state

        # Validate transition
        if new_state not in allowed_transitions[current_state]:
            return {
                "error": f"Invalid transition from {current_state} to {new_state}"
            }

        # Update workflow state
        cur.execute(
            "UPDATE workflows SET current_state = %s WHERE id = %s;",
            (new_state, workflow_id)
        )

        # Insert history record
        cur.execute(
            """
            INSERT INTO workflow_states (workflow_id, state)
            VALUES (%s, %s);
            """,
            (workflow_id, new_state)
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

    return {
        "workflow_id": workflow_id,
        "new_state": new_state
    }





# Get workflow with full state history
@app.get("/workflows/{workflow_id}")
def get_workflow(
    workflow_id: int,
    current_user_id: int = Depends(verify_token)
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT w.id, w.name, w.current_state, ws.state, ws.changed_at
            FROM workflows w
            LEFT JOIN workflow_states ws
            ON w.id = ws.workflow_id
            WHERE w.id = %s
            ORDER BY ws.changed_at;
            """,
            (workflow_id,)
        )

        rows = cur.fetchall()

        if not rows:
            return {"error": "Workflow not found"}

        workflow_info = {
            "workflow_id": rows[0][0],
            "name": rows[0][1],
            "current_state": rows[0][2],
            "history": []
        }

        for row in rows:
            workflow_info["history"].append({
                "state": row[3],
                "changed_at": row[4]
            })

    finally:
        cur.close()
        conn.close()

    return workflow_info
