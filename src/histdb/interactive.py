from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:////home/dani/.histdb/zsh-history.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()
breakpoint()
