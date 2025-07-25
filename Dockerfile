FROM public.ecr.aws/lambda/python:3.12

# Copia requirements.txt e instala dependências
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# Copia o código da função
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Define o handler
CMD [ "lambda_function.lambda_handler" ]
