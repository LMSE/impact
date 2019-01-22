# coding=utf-8
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

def bind_engine(db_path='sqlite:///default_impt.db',echo=False):
    engine = create_engine(db_path, echo=echo)
    return engine


def create_session(engine='default'):
    from sqlalchemy.orm import sessionmaker

    if engine == 'default':
        engine = bind_engine()

    # create_db()
    Session = sessionmaker(bind=engine,autoflush=True,expire_on_commit=False)
    return Session()


def create_db():
    Base.metadata.drop_all(bind_engine())
    Base.metadata.create_all(bind_engine())

session = create_session()

# Code to remove duplicates and consolidate references to common elements in database
# @event.listens_for(session, 'before_flush')
# def remove_duplicates(session, flush_context, instances):
#     for cls in [ti.Environment, ti.Media, ti.Strain]:
#         all_cls_objects = [obj for obj in session if isinstance(obj,cls)]
#         uniques = list(set(all_cls_objects))
#         print(uniques)
#         for unique in uniques:
#             print('-----------',id(unique),str(unique))
#             matching = [obj for obj in all_cls_objects if obj == unique]
#             for obj in [obj for obj in matching if obj is not unique]:
#                 session.expunge(obj)
#                 print(id(obj))

# @event.listens_for(mapper, 'init')
# def auto_add(target, args, kwargs):
#     session.add(target)