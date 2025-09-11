from extensions import db

class Student(db.Model):
    __tablename__ = "students"
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(120), nullable = False)
    age = db.Column(db.Integer, nullable = False)
    grade = db.Column(db.String(12), nullable = False)
    email = db.Column(db.String(200), nullable = False, unique = True)


    def to_dict(self):
        return {
            "id": self.id,
            "name" : self.name,
            "age" : self.age,
            "grade" : self.grade,
            "email" : self.email
        }
        
        