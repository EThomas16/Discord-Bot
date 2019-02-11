from discord import utils
from PIL import Image

def check_roles(roles: list, author: object) -> list:
    role_checks = []
    for role in roles:
        to_append = True
        if utils.get(author.roles, name=role) is None:
            to_append = False
        role_checks.append(to_append)
    
    return role_checks 

def clear_file(file_path: str):
    file_to_clear = open(file_path, 'w')
    file_to_clear.close()

def make_gif(file_path: str):
    sequence = []
    image = Image.open(file_path)