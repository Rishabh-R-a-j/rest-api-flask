from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models.store import StoreModel
from schemas import StoreSchema

blp = Blueprint("stores", __name__, description="Operations on store and items")


@blp.route("/store/<string:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted successfully"}


@blp.route("/store")
class StoreList(MethodView):
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, requestdata):
        store = StoreModel(**requestdata)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A store with that name already exist.")
        except SQLAlchemyError:
            abort(500, message="An error occured creating the store.")
        return store

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()
