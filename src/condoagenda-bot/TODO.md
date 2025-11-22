# -- V0.1
- [X] Criar agendamento
- [X] Integração com whatsapp completa (INICIAR AUTOMATICAMENTE)

# -- V0.2
- [X] Colocar step "Te ajudo em algo mais? (Finalizar atendimento, Realizar outro agendamento)"
- [ ] Criar endpoint unico que vai retornar a data e quantidade de slots disponivel em cada dia ordernado em ordem HOJE, AMANHA, ..., já com a regra de negocio de qual deve ser os dias (week, or next 7 days) 
- [ ] Integrar meus agendamentos ativos (Mostrar em forma de texto e riscado caso já tenha passado por exemplo) (Mostrar apenas da semana atual)

# -- V1
- [ ] WhatsApp Enquetes
- [ ] Melhorias nas mensagens de envio de usuario (Validar com outros usuários) (Ruan, Lanna, Pedro Guedes, Lucas, ...)

IDEIA:
- [ ] Mostrar um numero de horarios disponiveis para cada data para facilitar o usuario escolher um horario que tenha opções válidas.
- [ ] Não Mostrar datas que não tenha mais horários disponiveis
---

- [ ] Problema: Numero do apartamento não existe, horário conflitante, maximo de agendamentos feitos.
    - [ ] Solução: Continuar o workflow normalmente porem não fazer NADA
    - [ ] Solução 2: Melhorar para ter um feedback de erro

- [ ] Pitch deck + vídeo de apresentação (Slide de proposta de forma professional)
- [ ] Testes finais colocar Lanna para testar realizar agendamentos, tentar "quebrar o sistema"
- [ ] Lidar com erros de horario conflitante, apartamento invalido, nenhum horario disponivel
SOLUCAO PORCA: Retornar um erro e resetar o workflow por exemplo em casos de erro
- [ ] Auditoria simples (por exemplo qual foi o numero que realizou x ação no sistema)
- [ ] Integrar com os lembrete de agendamento
--
- [ ] Logs internos para visualizar o que ocorreu a cada etapa em qual etapa atual do workflow...
- [ ] Integração no grupo do whatsapp

# -- V2
- [ ] Criar um visualizador em tempo real das pipeline mostrando por exemplo o status
- [ ] O event handler não é necessário e ele é limitado pelas ações acho que ele é bom para outros tipos de integração como o progress,
porém regras de negocio pela flexibilidade de controlar o workflow seria melhor uma novo Nó
- [ ] DESAFIO: Compartilhar essa busca de dado de modo que as outros steps consigam utilizar o valor sem precisar buscar novamente