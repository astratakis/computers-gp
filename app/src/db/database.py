from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask import request
import re

import logging

DATABASE_URL = "postgresql+psycopg2://user:password@192.168.199.99:5432/masterdatabase"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def database_exception_handler(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Create a db session
        db = SessionLocal()
        try:
            # Pass the database session inside the wrapped function...
            return f(db, *args, **kwargs)
        except ValueError as ve:
            db.rollback()

            return {
                "url": request.url,
                "success": False,
                "result": {
                    "error": "Value Error",
                    "traceback": f"Error in {f.__name__}",
                    "message": str(ve)
                }
            }, 400
        
        except AttributeError as ae:
            db.rollback()

            return {
                "url": request.url,
                "success": False,
                "result": {
                    "error": "Value Error",
                    "traceback": f"Error in {f.__name__}",
                    "message": str(ae)
                }
            }, 404
        
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig)
            errors = {}
            m = re.search(r'Key \((.*?)\)=\(', error_msg)
            if m:
                column = m.group(1)
                errors[column] = [f"This {column.replace('_', ' ')} already exists."]
            else:
                errors['database'] = [error_msg]

            return {
                "url": request.url,
                "success": False,
                "result": {
                    "error": "Database Integrity Error",
                    "traceback": f"Error in {f.__name__}",
                    "message": str(e),
                    "elements": errors
                }
            }, 405

        except Exception as e:
            db.rollback()

            logging.error(str(e))
            
            return {
                "url": request.url,
                "success": False,
                "result": {
                    "error": "Internal Server Error",
                    "traceback": f"Error in {f.__name__}",
                    "message": str(e)
                }
            }, 500

        finally:
            # Ensure session is closed
            db.close()

    return wrapper
