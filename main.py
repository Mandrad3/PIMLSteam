import numpy as np
import pandas as pd
from fastapi import FastAPI

df_steam = pd.read_csv('./Data/steam_games.csv')

# Realiza la conversión de precio en df_steam
df_steam['price'] = df_steam['price'].apply(lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) and x.replace('$', '').replace(',', '').replace('.', '').isdigit() else 0.0)

# Otras lecturas de datos...

app = FastAPI()

@app.get("/userdata/{user_id}")
async def userdata(user_id: str):
    try:
        Cantidad = 0
        recommend_count = 0
        total_reviews = 0
        item_ids = set()

        # Configura el tamaño del lote para la lectura de reviews
        chunk_size = 100000
        user_reviews_generator = pd.read_csv('./Data/reviews.csv', chunksize=chunk_size)

        for chunk in user_reviews_generator:
            user_reviews = chunk[chunk['user_id'] == user_id]

            # Procesa los datos del lote actual
            Cantidad += user_reviews.merge(df_steam[['id', 'price']], left_on='item_id', right_on='id', how='inner')['price'].sum()
            recommend_count += user_reviews['recommend'].sum()
            total_reviews += len(user_reviews)
            item_ids.update(user_reviews['item_id'].unique())

        #Calcula el porcentage de recomendaciones
        if total_reviews > 0:
            porcentaje = (recommend_count / total_reviews) * 100
        else:
            porcentaje = 0
        #Cuenta los numeros de items
        cantidad_de_items = len(item_ids)

        user_data = {
            "Cantidad de dinero gastado": Cantidad,
            "recommend_porcentaje": porcentaje,
            "cantidad de items": cantidad_de_items
        }

        return user_data

    except Exception as e:
        return {"message": f"Error: {str(e)}"}

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Cargar el DataFrame df_steam desde tu archivo CSV
df_steam2 = pd.read_csv('./Data/steam_games.csv')

@app.get("/recomendacion_juego/{product_id}")
async def recomendacion_juego(product_id: int):
    try:
        # Obtener el juego de referencia
        target_game = df_steam2[df_steam2['id'] == product_id]

        if target_game.empty:
            return {"message": "No se encontró el juego de referencia."}

        # Combinar etiquetas (tags) y géneros en una sola cadena de texto
        target_game_tags_and_genres = ' '.join(target_game['tags'].fillna('').astype(str) + ' ' + target_game['genres'].fillna('').astype(str))

        # Crear un vectorizador TF-IDF
        tfidf_vectorizer = TfidfVectorizer()

        # Configurar el tamaño del lote para la lectura de juegos
        chunk_size = 100  # Puedes ajustar según tus necesidades
        similarity_scores = []

        # Procesar los juegos por lotes utilizando chunks
        for chunk in pd.read_csv('./Data/steam_games.csv', chunksize=chunk_size):
            # Combinar etiquetas (tags) y géneros de los juegos en una sola cadena de texto
            chunk_tags_and_genres = ' '.join(chunk['tags'].fillna('').astype(str) + ' ' + chunk['genres'].fillna('').astype(str))

            # Aplicar el vectorizador TF-IDF al lote actual de juegos y al juego de referencia
            tfidf_matrix = tfidf_vectorizer.fit_transform([target_game_tags_and_genres] + [chunk_tags_and_genres])

            # Calcular la similitud entre el juego de referencia y los juegos del lote actual
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Agregar las puntuaciones de similitud a la lista
            similarity_scores.append(similarity_matrix[1][0])

        if similarity_scores:
            # Obtener los índices de los juegos más similares
            similar_games_indices = np.argsort(similarity_scores)[::-1]

            # Recomendar los juegos más similares (ajustar el número de recomendaciones según lo necesites)
            num_recommendations = 5
            recommended_games = df_steam2.loc[similar_games_indices[:num_recommendations], ['app_name', 'id']]

            # Devolver la lista de juegos recomendados
            return recommended_games.to_dict(orient='records')

        return {"message": "No se encontraron juegos similares."}

    except Exception as e:
        return {"message": f"Error: {str(e)}"}



