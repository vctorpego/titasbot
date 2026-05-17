from pathlib import Path
from dotenv import load_dotenv

# Importações do seu projeto TitãsBot
from app.application.chat_service import TitasBotService
from app.infrastructure.settings import get_settings

# Importações do DeepEval
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

def test_titasbot_rag():
    # 1. Carregar as variáveis de ambiente
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)

    # 2. Inicializar as configurações e instanciar o bot
    settings = get_settings()
    bot = TitasBotService(settings)

    pergunta = "Qual foi a classificação da equipe na temporada de 2024?"

    # 3. Fazer a pergunta usando a sua orquestração atual
    resultado = bot.ask(question=pergunta)

    # DICA PRO: O DeepEval exige que o 'retrieval_context' seja uma lista de strings (textos).
    # Se 'resultado.source_chunks' for uma lista de objetos, você precisará extrair apenas o texto.
    # Exemplo: contextos = [chunk.text for chunk in resultado.source_chunks]
    contextos = [chunk.content for chunk in resultado.chunks]

    # 4. Inicializar as métricas de avaliação
    # O threshold (0.0 a 1.0) define a nota mínima para o teste passar.
    # 0.7 (70%) é um padrão rigoroso e excelente para começar.
    metrica_fidelidade = FaithfulnessMetric(threshold=0.7)
    metrica_relevancia = AnswerRelevancyMetric(threshold=0.7)

    # 5. Criar o caso de teste para o DeepEval
    test_case = LLMTestCase(
        input=pergunta,
        actual_output=resultado.answer,
        retrieval_context=contextos
    )

    # 6. Rodar as avaliações semânticas
    assert_test(test_case, [metrica_fidelidade, metrica_relevancia])