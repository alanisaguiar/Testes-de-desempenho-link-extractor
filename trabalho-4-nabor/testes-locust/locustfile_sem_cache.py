#Comportamento do usuário virtual:
#Realiza 10 invocações sequenciais ao serviço de extração de links, passando uma URL diferente a cada requisição.

#Diferença em relação ao script COM cache:
#O serviço de extração de links é apontado para uma instância sem Redis, forçando toda requisição a buscar os dados diretamente na web.

from locust import HttpUser, task, between
import random

# 10 URLs distintas usadas em cada sequência de invocações
URLS = [
    "https://www.python.org",
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://docs.docker.com",
    "https://redis.io",
    "https://flask.palletsprojects.com",
    "https://www.ruby-lang.org",
    "https://microservices.io",
    "https://play-with-docker.com",
    "https://hub.docker.com",
]


class LinkExtractorUserNoCache(HttpUser):
    #Usuário virtual que extrai links de 10 URLs distintas por ciclo.

    wait_time = between(0.5, 1.5)   #tempo de espera entre tarefas

    @task
    def extract_links_sequence_no_cache(self):
        #Sequência de 10 invocações
        shuffled = URLS.copy()
        random.shuffle(shuffled)    #ordena aleatoriamente para simular usuários reais

        for url in shuffled:
            #Parâmetro nocache=1 garante bypass do cache no servidor
            encoded_url = url.replace("://", "%3A%2F%2F").replace("/", "%2F")
            with self.client.get(
                f"/api/{encoded_url}?nocache=1",
                name="/api/[url]?nocache=1",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Status inesperado: {response.status_code}"
                    )
