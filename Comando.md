Vamos mudar o sistema logico de agentes

Novo sistema

Agente supervisor vai mudar para intermediador, faz mais sentido, ele vai abstrair a comunicação entre agentes para que o usuario tenha uma conversa natural com ele

Agente intermediador vai ser o agente que vai receber a solicitação do usuario e vai enviar para o agente que vai executar a tarefa

Teremos um agente central onde vai convergir todas as respostas vindas dos subagentes, ele vai entregar as respostas de forma organizada e coerente



base = gemini-2.5-flash-lite

medio = gemini-2.5-flash

avançado = gemini-2.5-pro

Logica de escolha de modelos segundo a complexidade da tarefa ou seja, não é a ferramenta que chama o modelo segundo a tarefa, mas a complexidade define o modelo e o modelo usa a ferramenta necessaria, por exemplo, o modelo de base pode ser usar qualquer ferramenta, assim como o medio e o avançado

Multiplas apis

As requisições vão ser feita da seguinte forma

Tenho por exemplo 3 apis

api-base

api-base-2

api-medio

api-medio-2

api-avançado
api-avançado-2

Cada api tem a funão segundo o modelo, a api -2, é um backup, ou seja, se a api-base não funcionar, a api-base-2 vai ser usada, e assim por diante
Vamos manter o rate limite para api base de 60 requisições por minuto

Para a api medio, vamos manter o rate limite de 30 requisições por minuto

Para a api avançado, vamos manter o rate limite de 10 requisições por minuto

Quando o servidor identificar que o rate limite foi atingido, ele troca a chave em uso para continuar a requisição

Os modelos não podem usar a api de outro modelo, por exemplo, o modelo de base não pode usar a api de médio assim por diante

Esse sistema deve funcionar de forma que varias ferramentas podem ser incluidas no processo de forma facil sem tanta codificação, para que elas funcione quase sempre de forma independente, mas sempre esperando retorno do modelo a ser usado



