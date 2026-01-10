from flask import Blueprint, render_template, request, redirect, url_for
from app.src import db
from app.src.models.game import Game

game_bp = Blueprint("game", __name__)

@game_bp.route("/admin/games")
def admin_games():
    games = Game.query.all()
    return render_template("admin_games.html", games=games)

@game_bp.route("/admin/games/add", methods=["POST"])
def add_game():
    game = Game(
        name=request.form["name"],
        price=request.form["price"]
    )
    db.session.add(game)
    db.session.commit()
    return redirect(url_for("game.admin_games"))
