from locust import HttpUser, task, TaskSet, between

# Esta é a sequência de 10 URLs que vamos testar 
URLS_PARA_TESTAR = [
    "/wiki/Brasil",
    "/wiki/Portugal",
    "/wiki/Inteligência_artificial",
    "/wiki/Docker_(software)",
    "/wiki/Python_(linguagem_de_programação)",
    "/wiki/Ruby_(linguagem_de_programação)",
    "/wiki/PHP",
    "/wiki/Redis",
    "/wiki/Locust_(software)",
    "/wiki/Fortaleza"
]

class LinkExtractorTaskSet(TaskSet):
    """
    Esta TaskSet define o comportamento sequencial do utilizador.
    Ele vai visitar todas as 10 URLs, uma após a outra.
    """

    def on_start(self):
        # Inicia o contador de índice da URL no início de cada sequência
        self.url_index = 0

    @task
    def extract_links(self):
        """
        Esta tarefa extrai os links de uma URL da lista.
        """
        if self.url_index < len(URLS_PARA_TESTAR):
            url_to_test = URLS_PARA_TESTAR[self.url_index]

            # O frontend em PHP espera que a URL seja passada como um parâmetro 'url'
            # O host (ex: http://www.wikipedia.org) será o alvo do nosso teste.
            # A API do Link Extractor espera a URL completa.
            full_url_to_extract = f"https://pt.wikipedia.org{url_to_test}"

            # O endpoint do frontend é /index.php
            # Fazemos um POST para /index.php, enviando a 'url' que queremos extrair
            self.client.get(
                "/index.php",
                params={"url": full_url_to_extract},
                name=f"Extrair: {url_to_test}"
            )

            # Avança para a próxima URL da lista
            self.url_index += 1
        else:
            # Quando o utilizador "termina" a sequência de 10, ele interrompe
            # e o Locust irá criar um novo utilizador que começa do zero.
            self.interrupt()

class WebsiteUser(HttpUser):
    """
    O utilizador virtual que executa o conjunto de tarefas.
    """
    tasks = [LinkExtractorTaskSet]
    # Espera entre 1 e 3 segundos entre cada sequência de 10 invocações
    wait_time = between(1, 3)