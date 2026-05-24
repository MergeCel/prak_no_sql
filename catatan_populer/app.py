from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

MONGO_FILE = "database/mongodb_data.json"
REDIS_FILE = "database/redis_data.json"


def read_json(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as file:
        try:
            return json.load(file)
        except:
            return []


def write_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


@app.route("/")
def home():
    return {
        "message": "Aplikasi Catatan Populer"
    }

@app.route("/tambah", methods=["POST"])
def tambah_catatan():

    data = request.json

    judul = data.get("judul")
    isi = data.get("isi")

    if not judul or not isi:
        return jsonify({
            "error": "Judul dan isi wajib diisi"
        }), 400

    mongodb_data = read_json(MONGO_FILE)

    catatan_baru = {
        "judul": judul,
        "isi": isi,
        "views": 0
    }

    mongodb_data.append(catatan_baru)

    write_json(MONGO_FILE, mongodb_data)

    return jsonify({
        "message": "Catatan berhasil ditambahkan",
        "data": catatan_baru
    })


@app.route("/catatan", methods=["GET"])
def lihat_catatan():

    mongodb_data = read_json(MONGO_FILE)

    return jsonify(mongodb_data)


@app.route("/populer", methods=["GET"])
def catatan_populer():

    redis_cache = read_json(REDIS_FILE)

    if redis_cache:
        return jsonify({
            "source": "Redis Cache",
            "data": redis_cache
        })

    mongodb_data = read_json(MONGO_FILE)

    populer = sorted(
        mongodb_data,
        key=lambda x: x["views"],
        reverse=True
    )

    populer = populer[:3]
    write_json(REDIS_FILE, populer)

    return jsonify({
        "source": "MongoDB",
        "data": populer
    })


@app.route("/view/<judul>", methods=["POST"])
def tambah_view(judul):

    mongodb_data = read_json(MONGO_FILE)

    ditemukan = False

    for catatan in mongodb_data:
        if catatan["judul"].lower() == judul.lower():
            catatan["views"] += 1
            ditemukan = True
            break

    if not ditemukan:
        return jsonify({
            "error": "Catatan tidak ditemukan"
        }), 404

    write_json(MONGO_FILE, mongodb_data)

    # Reset cache Redis
    write_json(REDIS_FILE, [])

    return jsonify({
        "message": f"View catatan '{judul}' bertambah"
    })


if __name__ == "__main__":
    app.run(debug=True)