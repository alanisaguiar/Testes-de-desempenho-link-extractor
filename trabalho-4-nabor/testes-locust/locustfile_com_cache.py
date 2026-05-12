# Realiza 10 invocações sequenciais ao serviço de extração de links passando uma URL diferente a cada requisição.

from locust import HttpUser, task, between, events
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


class LinkExtractorUser(HttpUser):
    #Usuário virtual que extrai links de 10 URLs distintas por ciclo.
  
    wait_time = between(0.5, 1.5)   #tempo de espera entre tarefas 

    @task
    def extract_links_sequence(self):
        #Sequência de 10 invocações
        shuffled = URLS.copy()
        random.shuffle(shuffled)   #ordena aleatoriamente para simular usuários reais

        for url in shuffled:
            encoded_url = url.replace("://", "%3A%2F%2F").replace("/", "%2F")
            with self.client.get(
                f"/api/{encoded_url}",
                name="/api/[url]",          #agrupa métricas sob o mesmo nome
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Status inesperado: {response.status_code}"
                    )
