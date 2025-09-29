ARG PYTHON_VERSION=3.12

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION} AS base

ARG SRC_PATH=.

# Copy python project
COPY ${SRC_PATH} ${LAMBDA_TASK_ROOT}

RUN pip install -e . \
    && pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt


CMD [ "aopcs_lambda/src/main.handler" ]
