from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    jwt_required,
)
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema, userret

blp = Blueprint("Users", "users", description="Operations on users")


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel(
            name=user_data["name"],
            password=pbkdf2_sha256.hash(user_data["password"]),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            abort(400, message="Integrity Error")
        except SQLAlchemyError:
            abort(500, message="An error occured while creating user")
        else:
            return {"Message": "User Created Successfully"}, 201


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def post(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        try:
            db.session.delete(user)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Some error occured while deleting user from database.")
        else:
            return {"message": "User deleted successfully."}, 200

    @blp.response(200, userret)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user


@blp.route("/user")
class GetUser(MethodView):
    @blp.response(200, userret(many=True))
    def get(self):
        user = UserModel.query.all()
        return user


@blp.route("/login")
class login(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(user_data["name"] == UserModel.name).first()
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.id), fresh=True)
            refersh_token = create_refresh_token(identity=str(user.id))
            return {"access_token": access_token, "refresh_token": refersh_token}

        abort(401, message="Invalid credentials.")


@blp.route("/logout")
class logout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "successfully logged out."}


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def get(self):
        id = get_jwt().get("sub")
        access_token = create_access_token(identity=id, fresh=False)
        return {"access_token": access_token}
