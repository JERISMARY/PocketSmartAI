import shutil, os

src_dir = r'C:/Users/jeris/.gemini/antigravity-ide/brain/85cdf555-0169-4e13-99fd-26bef01a4a7d'
dst_dir = r'C:/Users/jeris/OneDrive/jesus/sample/app/static/images'

os.makedirs(dst_dir, exist_ok=True)

copies = [
    ('party_planner_card_1790961377735.png', 'party_planner.png'),
    ('home_planner_card_1790961448150.png',  'home_planner.png'),
    ('jewelry_planner_card_1790961460661.png','jewelry_planner.png'),
]

for src_name, dst_name in copies:
    src = os.path.join(src_dir, src_name)
    dst = os.path.join(dst_dir, dst_name)
    shutil.copy2(src, dst)
    print(f'Copied {dst_name}')

print('All done.')
