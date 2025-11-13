FROM  joyzoursky/python-chromedriver:3.8
WORKDIR  /
COPY  .  /
RUN  pip  install  -r  requirements.txt
CMD  ["python",  "bot.py"]