# app/routes.py
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.models import Student
from extensions import db
import os

bp = Blueprint('api', __name__)


@bp.get("/health")
def health():
    return jsonify({
        "status" : "ok",
        "service" : current_app.config.get("APP_NAME", "student-api"),
        "version" : current_app.config.get("API_VERSION"),
        "env" : current_app.config.get("ENV_NAME", "development"),
        "owner" : current_app.config.get("APP_OWNER"),
        "build_num" : current_app.config.get("BUILD_NUM")
    }), 200


@bp.get("/db/health")
def db_health():
    
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"db": "up"}), 200
    except Exception as e:
        return jsonify({"db": "down", "detail" : str(e)}), 500

@bp.get("/students")
def list_students():
    items = Student.query.order_by(Student.id.asc()).all()
    return jsonify([s.to_dict() for s in items]), 200

@bp.post("/students")
def create_student():
    data = request.get_json(silent=True) or {}
    
    required = ["name", "age", "grade", "email"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error" : "validation_error",
                        "detail" : f"Missing fields: {', '.join(missing)}"
                        }), 400
    
    try:
        age = int(data["age"])
    except(TypeError, ValueError):
        return jsonify({"error" : "validation_error", "detail" : "age should be int"}), 400
    
    student = Student(
        name=str(data["name"]).strip(),
        age=int(data["age"]),
        grade=str(data['grade']).strip(),
        email=str(data["email"]).strip().lower()
    )
    
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error" : "conflict", "detail" : "email already exists"}), 409
    
    return jsonify(student.to_dict()), 201


@bp.get("/students/<int:id>")
def get_student(id):
    student = db.session.get(Student, id)
    
    if student is None:
        return jsonify({"error" : "not_found"}), 404
    else:
        return jsonify(student.to_dict()), 200        
    
    
@bp.delete("/students/<int:id>")
def delete_student(id):
    
    student = db.session.get(Student, id)
    
    if student is None:
        return jsonify({"error": "not_found"}), 404
    else:
        db.session.delete(student)
        db.session.commit()
        return "", 204

@bp.put("/students/<int:id>")
def update_student(id):
    
    student = db.session.get(Student, id)
    
    if student is None:
        return jsonify({"error":"not_found"}), 404
    
    data = request.get_json(silent=True) or {}
    
    if "name" in data:
        student.name = str(data["name"]).strip()
    
    if "email" in data:
        
        student.email = str(data["email"]).strip().lower()
        
    if "grade" in data:
        student.grade = str(data["grade"]).strip()
        
    if "age" in data:
        try:
            student.age = int(data["age"])
        except ( TypeError, ValueError ):
            return jsonify({"error" : "validation_error",
                            "detail": "age must be int"}), 400

    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error" : "conflict", "detail" : "email already exists"}), 409
              
    return jsonify(student.to_dict()), 200

