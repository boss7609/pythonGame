#Excel優化-根目錄
#載入圖片-可讀性優化
#題目判斷優化-自動換行
#選武器模式優化-可讀性優化
#大爆炸功能優化-PASS
#產生粒子特效-PASS
#高分存儲-可讀性優化
#優化精靈

import os
import pandas as pd
import pygame
import random
import sys
import json
from pygame.locals import *
import math

pygame.init()  
# === 常數定義 ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
ITEM_SPAWN_RATE = 0.005
MONSTER_SPAWN_RATE = 0.015
ROCK_SPAWN_RATE = 0.02
SPECIAL_COOLDOWN_FRAMES = 180
icon = pygame.image.load('pic/Favicon.ico')
pygame.display.set_icon(icon)
# === 顏色定義 ===
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
UI_FONT = pygame.font.Font(None, 36)

# === 讀取 Excel 題庫 ===
def load_historical_questions_from_excel():
    file_path = os.path.join(os.getcwd(), "data/historical_questions.xlsx")
    if not os.path.exists(file_path):
        print(f"[ERROR] 文件不存在: {file_path}")
        return []
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        print(f"[ERROR] 讀取 Excel 失敗: {e}")
        return []
    
    required_columns = ["題目", "A", "B", "C", "D", "答案", "解答"]
    if not all(col in df.columns for col in required_columns):
        print(f"[ERROR] Excel 缺少必要欄位: {required_columns}")
        return []
    
    questions = []
    for _, row in df.iterrows():
        questions.append({
            "question": str(row['題目']),
            "choices": {
                'A': str(row['A']),
                'B': str(row['B']),
                'C': str(row['C']),
                'D': str(row['D'])
            },
            "answer": str(row['答案']).strip().upper(),
            "explanation": str(row['解答'])
        })
    
    return questions

# === 載入圖片 ===
def load_image(path, size, shape='plane'):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except (pygame.error, FileNotFoundError) as e:
        print(f"[WARNING] 無法載入圖片: {path}，使用預設形狀代替 ({shape})。錯誤訊息: {e}")

        # 建立透明背景
        surf = pygame.Surface(size, pygame.SRCALPHA)

        # 根據類型畫替代圖形
        if shape == 'plane':
            pygame.draw.polygon(
                surf, (255, 0, 0),
                [(size[0] // 2, 0), (0, size[1]), (size[0], size[1])]
            )
        elif shape == 'rock':
            pygame.draw.circle(
                surf, (128, 128, 128),
                (size[0] // 2, size[1] // 2), min(size) // 2
            )
        elif shape == 'bullet':
            pygame.draw.rect(
                surf, (255, 255, 255),
                surf.get_rect()
            )
        elif shape == 'item':
            pygame.draw.rect(
                surf, (200, 200, 0),
                surf.get_rect()
            )

        return surf

# === 題目正確判斷 ===
def run_quiz(screen, font, q):
    # 顏色設定
    BLACK, WHITE = (0, 0, 0), (255, 255, 255)
    options = ['A', 'B', 'C', 'D']
    selected = None
    font = pygame.font.SysFont("Microsoft JhengHei", 28)

    while True:
        screen.fill(BLACK)  # 填滿背景為黑色

        # 顯示題目，並記錄題目最後一行的底部y座標
        y = 50
        y += draw_text(screen, q['question'], font, WHITE, 50, y, 700)
        y += 30  # 題目和選項之間空一段距離

        # 顯示選項，每個選項之間留間距
        for i, k in enumerate(options):
            text = f"{i+1}. {q['choices'][k]}"
            height = draw_text(screen, text, font, WHITE, 50, y, 700)
            y += height + 20  # 每個選項之間再空一點

        pygame.display.flip()  # 更新螢幕

        # 等待玩家選擇答案
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()

            if e.type == KEYDOWN:
                if e.key in (K_1, K_KP1):
                    selected = 0
                if e.key in (K_2, K_KP2):
                    selected = 1
                if e.key in (K_3, K_KP3):
                    selected = 2
                if e.key in (K_4, K_KP4):
                    selected = 3

                if selected is not None:
                    # 顯示答對或答錯的訊息
                    result_text = ""
                    if options[selected] == q['answer']:
                        result_text = "O 答對了！"
                    else:
                        result_text = "X 答錯了！"

                    screen.fill(BLACK)  # 清空螢幕
                    # 顯示結果
                    result_font = pygame.font.SysFont("Microsoft JhengHei", 48)
                    result_rendered = result_font.render(result_text, True, WHITE)
                    result_rect = result_rendered.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 30))
                    screen.blit(result_rendered, result_rect)

                    # 顯示提示文字
                    prompt_text = "(按任意鍵繼續...)"
                    prompt_font = pygame.font.SysFont("Microsoft JhengHei", 20)
                    prompt_rendered = prompt_font.render(prompt_text, True, WHITE)
                    prompt_rect = prompt_rendered.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 30))
                    screen.blit(prompt_rendered, prompt_rect)

                    pygame.display.flip()  # 更新螢幕

                    # 等待玩家按鍵繼續
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == KEYDOWN:
                                waiting = False  # 退出等待，繼續遊戲
                    return options[selected] == q['answer']  # 回傳結果

# === 選武器模式 ===
def choose_weapon_mode(screen):
    font = pygame.font.SysFont('Microsoft JhengHei', 36)
    options = ['1. 貫穿單發', '2. 快速雙發', '3. 三發散射', '4. 追蹤子彈', '5. 波動射擊']
    selected_mode = None
    BLACK, WHITE = (0, 0, 0), (255, 255, 255)

    while selected_mode is None:
        screen.fill(BLACK)
        y = 50
        y += draw_text(screen, '選擇你的武器模式:', font, WHITE, 50, y, 700)
        y += 30
        for opt in options:
            height = draw_text(screen, opt, font, WHITE, 50, y, 700)
            y += height + 20
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_1:
                    selected_mode = 1
                if e.key == K_2:
                    selected_mode = 2
                if e.key == K_3:
                    selected_mode = 3
                if e.key == K_4:
                    selected_mode = 4
                if e.key == K_5:
                    selected_mode = 5
    return selected_mode

# === 全局工具函數 ===
def draw_text(surface, text, font, color, x, y, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''
    for word in words:
        test_line = current_line + word + ' '
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:  # 避免添加空行
                lines.append(current_line)
            current_line = word + ' '
    if current_line:  # 添加最後一行
        lines.append(current_line)
    for i, line in enumerate(lines):
        rendered = font.render(line.strip(), True, color)
        surface.blit(rendered, (x, y + i * font.get_height()))
    return len(lines) * font.get_height()  # 回傳總高度

# === 大爆炸功能 ===
def historical_attack(all_sprites, rocks, monsters, enemy_bullets, particles, sound, score):
    temp_score = 0
    for group in (rocks, monsters):
        for e in list(group):
            create_particles(particles, all_sprites, e.rect.center)
            temp_score += 300 if hasattr(e, 'health') else 20  # 隕石 +20，小怪/Boss +300
            e.kill()
    score += min(temp_score, 800)  # 限制最多 800 分
    for b in list(enemy_bullets):
        b.kill()
    if sound:
        sound.play()
    return score

# === 產生粒子特效 ===
def create_particles(particles, all_sprites, position):
    for _ in range(10):
        p = Particle(*position)
        particles.add(p)
        all_sprites.add(p)

# === 物件生成 ===
def spawn_objects(game_state, all_sprites, items, monsters, rocks, boss_group, images, level, enemy_bullets, sounds):
    # 生成物品
    if random.random() < ITEM_SPAWN_RATE:
        it = Item(SCREEN_WIDTH, life_img=images['life'], wp_img=images['weapon'], quiz_img=images['quiz'])
        all_sprites.add(it)
        items.add(it)

    # 生成普通小兵
    if random.random() < MONSTER_SPAWN_RATE:
        m = Monster(images['monster'], game_state.diff, level, images['enemy_bullet'], all_sprites, enemy_bullets)
        all_sprites.add(m)
        monsters.add(m)
    
    # 生成隕石
    if random.random() < ROCK_SPAWN_RATE:
        r = Rock(images['rock'], game_state.diff, level)
        all_sprites.add(r)
        rocks.add(r)

    # 根據分數生成 Boss
    if game_state.score >= game_state.next_boss_score and game_state.score != 0:
        if not any(isinstance(x, Boss) for x in boss_group):
            b = Boss(images['boss'], game_state.diff, images['enemy_bullet'], all_sprites, enemy_bullets, sounds['shoot'])
            all_sprites.add(b)
            boss_group.add(b)
            rocks.add(b)
            interval = 500 + 250 * (game_state.level // 2)  # 動態間隔
            game_state.next_boss_score += interval
            print(f"生成 Boss，分數: {game_state.score}, 下一個目標: {game_state.next_boss_score}")
            
def handle_boss_defeat(boss_group, defeated_boss):
    if defeated_boss in boss_group:
        boss_group.remove(defeated_boss)
# === 處理物品撿取 ===
def handle_item_collisions(player, items, game_state, screen, font, questions, all_sprites, rocks, monsters, enemy_bullets, particles, explosion_sound):
    hits = pygame.sprite.spritecollide(player, items, True)
    for it in hits:
        if it.type == 'life':
            player.lives += 1
            player.health = min(player.health + 30, player.max_health)
        elif it.type == 'weapon':
            mode = choose_weapon_mode(screen)
            game_state.mode = mode
        elif it.type == 'quiz' and questions:
            q = random.choice(questions)
            if run_quiz(screen, font, q):
                game_state.score = historical_attack(all_sprites, rocks, monsters, enemy_bullets, particles, explosion_sound, game_state.score)

# === 處理玩家射擊 ===
def handle_player_shooting(player, keys, game_state, all_sprites, bullets, lasers, bullet_img, shoot_sound, monsters):
    if not hasattr(game_state, 'shoot_cooldown'):
        game_state.shoot_cooldown = 0
    if game_state.shoot_cooldown > 0:
        game_state.shoot_cooldown -= 1
        return

    if keys[K_SPACE]:
        cooldowns = {1: 8, 2: 4, 3: 7, 4: 12, 5: 20}  # 更新冷卻時間
        game_state.shoot_cooldown = cooldowns.get(game_state.mode, 8)

        if game_state.mode == 1:  # 貫穿單發：傷害 30
            b = Bullet(player.rect.centerx, player.rect.top, pygame.transform.scale(bullet_img, (8, 20)), damage=30, penetrate=True)
            all_sprites.add(b)
            bullets.add(b)
        elif game_state.mode == 2:  # 快速雙發：傷害 15
            for dx in [-10, 10]:
                b = Bullet(player.rect.centerx + dx, player.rect.top, bullet_img, damage=15)
                all_sprites.add(b)
                bullets.add(b)
        elif game_state.mode == 3:  # 三發散射：傷害 12
            for dx, dy in [(-10, -10), (0, -12), (10, -10)]:
                b = Bullet(player.rect.centerx + dx, player.rect.top, bullet_img, dx/2, dy, damage=12)
                all_sprites.add(b)
                bullets.add(b)
        elif game_state.mode == 4:  # 追蹤子彈：傷害 20
            target = None
            min_dist = float('inf')
            for m in monsters:
                dist = ((player.rect.centerx - m.rect.centerx)**2 + (player.rect.centery - m.rect.centery)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    target = m
            if target:
                b = Bullet(player.rect.centerx, player.rect.top, bullet_img, damage=20, track=True, target=target)
                all_sprites.add(b)
                bullets.add(b)
        elif game_state.mode == 5:  # 波動射擊：後續處理
            w = WaveBullet(player.rect.centerx, player.rect.top)
            all_sprites.add(w)
            bullets.add(w)

        if shoot_sound:
            shoot_sound.play()

# === 處理碰撞 ===
def handle_collisions(player, bullets, lasers, rocks, monsters, enemy_bullets, particles, all_sprites, game_state, explosion_sound, boss_group):
    for group in (rocks, monsters):
        hits = pygame.sprite.groupcollide(bullets, group, False, False)  # 子彈預設不消失
        for bl, lst in hits.items():
            for tgt in lst:
                if hasattr(tgt, 'health'):
                    tgt.health -= bl.damage
                    if tgt.health <= 0:
                        tgt.kill()
                        game_state.score += 300 if isinstance(tgt, Boss) else 100
                        if isinstance(tgt, Boss):
                            handle_boss_defeat(boss_group, tgt)
                else:
                    tgt.kill()
                    game_state.score += 30 if isinstance(bl, WaveBullet) else 20
                create_particles(particles, all_sprites, tgt.rect.center)
                if explosion_sound:
                    explosion_sound.play()
                # 處理子彈消失邏輯
                if isinstance(bl, WaveBullet):
                    continue  # WaveBullet 持續直到 duration 耗盡
                if not getattr(bl, 'penetrate', False):
                    bl.kill()
                else:
                    bl.damage = max(bl.damage // 2, 5)  # 貫穿子彈傷害減半

    # 雷射 vs rocks/monsters
    for group in (rocks, monsters):
        hits = pygame.sprite.groupcollide(lasers, group, False, False)
        for lb, lst in hits.items():
            for tgt in lst:
                if hasattr(tgt, 'health'):
                    tgt.health -= lb.damage
                    if tgt.health <= 0:
                        tgt.kill()
                        game_state.score += 300 if isinstance(tgt, Boss) else 100
                        if isinstance(tgt, Boss):
                            handle_boss_defeat(boss_group, tgt)
                else:
                    tgt.kill()
                    game_state.score += 30
                create_particles(particles, all_sprites, tgt.rect.center)
                if explosion_sound:
                    explosion_sound.play()

    # 敵人攻擊玩家
    if pygame.sprite.spritecollide(player, enemy_bullets, True):
        player.health -= 20
        if player.health <= 0:
            player.lives -= 1
            player.health = player.max_health
            if player.lives <= 0:
                save_high_score(game_state.score)
                return "game_over"

    # 玩家撞擊
    if pygame.sprite.spritecollide(player, rocks, True) or pygame.sprite.spritecollide(player, monsters, True):
        player.health -= 10
        if player.health <= 0:
            player.lives -= 1
            player.health = player.max_health
            if player.lives <= 0:
                save_high_score(game_state.score)
                return "game_over"

    return False

# === 更新等級 ===
def update_level(game_state):
    # 如果還沒設定初始門檻，設定一下
    if not hasattr(game_state, 'next_threshold'):
        game_state.next_threshold = 100  # 初始升級門檻分數
    # 玩家分數超過門檻時
    while game_state.score >= game_state.next_threshold:
        game_state.level += 1  # 升一級
        game_state.diff = 1 + game_state.score / 1000.0  # 難度也根據分數提升
        game_state.special = True  # 標記發生特殊事件
        
        # 更新下一個門檻，乘上1.2倍
        game_state.next_threshold = int(game_state.next_threshold * 1.2)

# === 高分存儲 ===
def load_high_score():
    try:
        with open('data/save.json', 'r') as f:
            data = json.load(f)
        return data.get('high_score', 0)  # 使用 .get() 避免不存在的key引發異常
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] 讀取高分失敗: {e}")
        return 0  # 如果讀取失敗，返回 0
def save_high_score(score):
    try:
        # 讀取現有高分
        hs = load_high_score()

        # 比較並保存高分
        with open('save.json', 'w') as f:
            json.dump({'high_score': max(score, hs)}, f)
    except Exception as e:
        print(f"[ERROR] 儲存高分失敗: {e}")

# === 精靈類別 ===
#玩家
class Player(pygame.sprite.Sprite):
    def __init__(self, img, w, h):
        super().__init__()
        self.image = img
        self.image.set_colorkey((255, 255, 255))  # 設置白色為透明色
        self.rect = img.get_rect(centerx=w // 2, bottom=h - 10)  # 設置初始位置
        self.speed = 8
        self.max_health = 100
        self.health = self.max_health
        self.lives = 3
    def move(self, controls):
        keys = pygame.key.get_pressed()
        if keys[controls['left']]:
            self.rect.x -= self.speed
        if keys[controls['right']]:
            self.rect.x += self.speed
    def update(self, controls=None):
        if controls:
            self.move(controls)
        # 限制玩家在螢幕範圍內移動
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        
#子彈
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, img, dx=0, dy=-10, damage=10, penetrate=False, track=False, target=None):
        super().__init__()
        self.image = img
        self.rect = img.get_rect(centerx=x, bottom=y)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.penetrate = penetrate  # 是否貫穿
        self.track = track  # 是否追蹤
        self.target = target  # 追蹤目標
        self.speed = 10  # 追蹤子彈總速度

    def move(self):
        if self.track and self.target and self.target.alive():
            # 計算朝目標的方向
            tx, ty = self.target.rect.center
            dx, dy = tx - self.rect.centerx, ty - self.rect.centery
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                self.dx = dx / dist * self.speed
                self.dy = dy / dist * self.speed
        self.rect.x += self.dx
        self.rect.y += self.dy

    def is_out_of_bounds(self, screen_rect):
        return not screen_rect.contains(self.rect)

    def update(self, *args):
        self.move()
        if self.is_out_of_bounds(pygame.display.get_surface().get_rect()):
            self.kill()
            self.kill()



class WaveBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 定義表面：100×100 像素（容納旋轉）
        self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.rect = pygame.Rect(0, 0, 100, 80)  # 碰撞範圍 100×80
        self.rect.centerx = x
        self.rect.bottom = y
        self.dy = -12  # 速度
        self.damage = 10  # 每幀傷害
        self.duration = 30  # 持續 0.5 秒
        self.frame = 0  # 動畫計數器
        self.draw_half_moon()  # 初始繪製

    def draw_half_moon(self):
        # 清空表面
        self.image.fill((0, 0, 0, 0))
        # 計算透明度（閃爍效果）
        alpha = 100 + 50 * (self.frame % 10 // 5)  # 100-150 交替
        # 外圓（作為月亮的外圓）
        outer_center = (50, 50)  # 圓心在表面中心
        outer_radius = 40  # 半徑
        # 內圓（作為月缺的部分，右側挖空）
        inner_center = (70, 50)  # 內圓中心右偏
        inner_radius = 40  # 內圓半徑，與外圓一樣大

        # 繪製外圓（綠色半月主體）只繪製上半部分
        pygame.draw.circle(self.image, (0, 255, 0, alpha), outer_center, outer_radius)

        # 使用遮罩來處理內圓，讓月缺完全消失下半圓部分
        pygame.draw.circle(self.image, (0, 0, 0, 0), inner_center, inner_radius)
        
        # 添加光暈（淡綠色外圍）
        pygame.draw.circle(self.image, (0, 255, 0, alpha // 2), outer_center, outer_radius + 3, width=3)

        # 旋轉表面，讓月缺朝下（這裡旋轉270度）
        self.image = pygame.transform.rotate(self.image, 270)
        
        # 更新 rect 保持 100×80
        old_center = self.rect.center
        self.rect = pygame.Rect(0, 0, 100, 80)
        self.rect.center = old_center

    def update(self, *args):
        self.rect.y += self.dy
        self.duration -= 1
        self.frame += 1
        self.draw_half_moon()  # 每幀重繪，實現閃爍
        if self.duration <= 0 or self.rect.bottom < 0:
            self.kill()




#雷射防護罩
class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        w = pygame.display.get_surface().get_width()
        self.image = pygame.Surface((w, 10), pygame.SRCALPHA)
        self.image.fill((0, 255, 0, 100))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.centery = y
        self.duration = 999  # 持續時間（約 16.65 秒）
        self.damage = 50
        self.dx = 0
        self.dy = -15  # 向上移動速度

    def check_duration(self):
        if self.duration <= 0:
            self.kill()
        else:
            self.duration -= 1

    def update(self, *args):
        self.rect.y += self.dy  # 實現移動
        self.check_duration()
        # 檢查是否超出螢幕
        if self.rect.bottom < 0:
            self.kill()
#隕石
class Rock(pygame.sprite.Sprite):
    def __init__(self, img, diff, level):
        super().__init__()
        w = pygame.display.get_surface().get_width()
        self.image = img
        self.rect = img.get_rect(x=random.randint(0, w-img.get_width()), y=-img.get_height())
        self.speed = 0.5 + diff * 0.5  # 優化速度計算方法

    def update(self, *args):
        self.rect.y += self.speed
        if self.rect.bottom > pygame.display.get_surface().get_height():  # 檢查 bottom 是否超出螢幕
            self.kill()
#敵機
class Monster(pygame.sprite.Sprite):
    def __init__(self, img, diff, level, enemy_bullet_img, all_sprites, enemy_bullets):
        super().__init__()
        self.screen_height = pygame.display.get_surface().get_height()
        self.screen_width = pygame.display.get_surface().get_width()
        self.image = img
        self.rect = img.get_rect(x=random.randint(0, self.screen_width - img.get_width()), y=-img.get_height())
        self.speed = (0.8 + level * 0.05) * diff
        self.max_health = 50 + level * 10
        self.health = self.max_health
        self.shoot_delay = 90
        self.timer = 0
        self.enemy_bullet_img = enemy_bullet_img
        self.all_sprites = all_sprites  # 儲存群組引用
        self.enemy_bullets = enemy_bullets  # 儲存群組引用

    def update(self, *args):
        self.rect.y += self.speed
        self.timer += 1
        if self.timer >= self.shoot_delay:
            self.timer = 0
            m_bullet = BossBullet(self.rect.centerx, self.rect.bottom, self.enemy_bullet_img, dx=0)
            self.all_sprites.add(m_bullet)  # 使用儲存的引用
            self.enemy_bullets.add(m_bullet)  # 使用儲存的引用

        if self.rect.top > self.screen_height:
            self.kill()
#BOSS
class Boss(pygame.sprite.Sprite):
    def __init__(self, img, diff, enemy_bullet_img, all_sprites, enemy_bullets, shoot_sound):
        super().__init__()
        self.screen_width = pygame.display.get_surface().get_width()
        self.image = img
        self.rect = img.get_rect(centerx=self.screen_width // 2, y=50)
        self.max_health = 500 * diff
        self.health = self.max_health
        self.speed = 2 * diff
        self.dir = 1
        self.timer = 0
        self.delay = 60
        self.enemy_bullet_img = enemy_bullet_img
        self.all_sprites = all_sprites  # 儲存群組引用
        self.enemy_bullets = enemy_bullets  # 儲存群組引用
        self.shoot_sound = shoot_sound  # 儲存音效引用

    def update(self, *args):
        self.rect.x += self.speed * self.dir
        if self.rect.left < 0 or self.rect.right > self.screen_width:
            self.dir *= -1
        self.timer += 1
        if self.timer >= self.delay:
            self.timer = 0
            self.shoot()

    def shoot(self):
        mode = random.choice(['normal', 'spread', 'rapid'])
        shoot_modes = {
            'normal': lambda: [BossBullet(self.rect.centerx, self.rect.bottom, self.enemy_bullet_img)],
            'spread': lambda: [BossBullet(self.rect.centerx, self.rect.bottom, self.enemy_bullet_img, dx) for dx in (-3, 0, 3)],
            'rapid': lambda: [BossBullet(self.rect.centerx, self.rect.bottom, self.enemy_bullet_img) for _ in range(3)],
        }
        bullets = shoot_modes.get(mode, lambda: [])()
        for b in bullets:
            self.all_sprites.add(b)  # 使用儲存的引用
            self.enemy_bullets.add(b)  # 使用儲存的引用
            if self.shoot_sound:
                self.shoot_sound.play()           
#Boss子彈
class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, enemy_bullet_img, dx: int = 0, dy: int = 5):
        super().__init__()
        self.image = enemy_bullet_img
        self.rect = self.image.get_rect(centerx=x, top=y)
        self.dx = dx
        self.dy = dy

    def update(self, *args):
        self.rect.x += self.dx
        self.rect.y += self.dy
        screen_height = pygame.display.get_surface().get_height()
        if self.rect.top > screen_height:
            self.kill()       
#物品life/weapon/quiz
class Item(pygame.sprite.Sprite):
    def __init__(self, w: int, life_img=None, wp_img=None, quiz_img=None, item_type: str = None):
        super().__init__()
        self.type = item_type or random.choice(['life', 'weapon', 'quiz'])
        if self.type == 'life':
            self.image = life_img
        elif self.type == 'weapon':
            self.image = wp_img
        elif self.type == 'quiz':
            self.image = quiz_img
        else:
            raise ValueError(f"Unknown item type: {self.type}")

        # 確保這裡的 w 是數字，而不是 Surface
        self.rect = self.image.get_rect(
            x=random.randint(0, w - self.image.get_width()),  # w 是一個整數
            y=-self.image.get_height()  # image.get_height() 返回的是整數
        )
        self.speed = random.randint(2, 4)

    def update(self, *args):
        self.rect.y += self.speed
        if self.rect.top > pygame.display.get_surface().get_height():
            self.kill()
#粒子
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, life=20, color_range=((200, 255), (0, 200), (0, 0)), speed_range=((-3, 3), (-5, 0))):
        super().__init__()
        self.size = random.randint(2, 5)
        self.image = self._create_image(color_range)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = [random.randint(*speed_range[0]), random.randint(*speed_range[1])]
        self.life = life

    def _create_image(self, color_range):
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color = (
            random.randint(*color_range[0]),
            random.randint(*color_range[1]),
            random.randint(*color_range[2])
        )
        pygame.draw.circle(surface, color, (self.size, self.size), self.size)
        return surface

    def update(self, *args):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        self.life -= 1
        if self.life <= 0:
            self.kill()
#資源優化
class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.images = {}
            cls._instance.sounds = {}
        return cls._instance

    def load_resources(self):
        self.images = {
            'plane': load_image('pic/plane.png', (50, 50), 'plane'),
            'bullet': load_image('pic/bullet.png', (5, 15), 'bullet'),
            'rock': load_image('pic/rock.png', (40, 40), 'rock'),
            'monster': load_image('pic/monster.png', (50, 50), 'rock'),
            'boss': load_image('pic/boss4.png', (100, 80), 'plane'),
            'life': load_image('pic/life.png', (30, 30), 'item'),
            'weapon': load_image('pic/weapon.png', (30, 30), 'item'),
            'quiz': load_image('pic/history_book.png', (30, 30), 'item'),
            'enemy_bullet': load_image('pic/enemy_bullet.png', (10, 20), 'bullet'),
            'background': load_image('pic/background.png', (SCREEN_WIDTH, SCREEN_HEIGHT), 'item')
        }
        self.sounds = {
            'shoot': pygame.mixer.Sound('sound/shoot.wav') if pygame.mixer.get_init() else None,
            'explosion': pygame.mixer.Sound('sound/explosion.wav') if pygame.mixer.get_init() else None
        }

# === 遊戲狀態封裝 ===
class GameState:
    def __init__(self):
        self.level = 1
        self.diff = 1.0
        self.special = False
        self.special_cooldown = 0
        self.mode = 1
        self.score = 0
        self.high_score = load_high_score()
        self.next_boss_score = 1000  # 初始 1000 分
#UI優化
def draw_ui(screen, score, player, level, high_score, special, font=UI_FONT):
    # 文字資訊區
    info_texts = [
        (f"Score: {score}", (10, 10)),
        (f"Level: {level}", (300, 10)),
        (f"High Score: {high_score}", (550, 10)),
    ]

    for text, pos in info_texts:
        screen.blit(font.render(text, True, WHITE), pos)

    # 特殊武器狀態
    laser_text = "READY" if special else "CHARGE"
    laser_color = GREEN if special else RED
    screen.blit(font.render(f"Laser: {laser_text}", True, laser_color), (10, 90))

    # 血量條
    bar_w, bar_h = 200, 10
    ratio = player.health / player.max_health
    pygame.draw.rect(screen, RED, (10, 50, bar_w * ratio, bar_h))
    pygame.draw.rect(screen, WHITE, (10, 50, bar_w, bar_h), 1)

    # 生命數
    screen.blit(font.render(f"Lives: {player.lives}", True, WHITE), (10, 70))

# === 背景 ===
def create_gradient_background(width, height, center_color=(0, 0, 100), edge_color=(0, 0, 0)):
    surface = pygame.Surface((width, height))
    mid_y = height // 2
    
    for y in range(height):
        # 計算從中間到邊緣的插值比例
        t = abs(y - mid_y) / mid_y  # 從 0（中間）到 1（邊緣）
        r = int(center_color[0] * (1 - t) + edge_color[0] * t)
        g = int(center_color[1] * (1 - t) + edge_color[1] * t)
        b = int(center_color[2] * (1 - t) + edge_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    
    return surface

# === 通用畫面管理函數 ===
def menu_screen(screen, title_text, buttons, subtitle_text=None, version_text=None, background_image=None, allow_esc_resume=False):
    clock = pygame.time.Clock()
    
    # 字體設定
    title_font = pygame.font.SysFont("Microsoft JhengHei", 72, bold=True)
    button_font = pygame.font.SysFont("Microsoft JhengHei", 36)
    subtitle_font = pygame.font.SysFont("Microsoft JhengHei", 24, bold=True)
    
    # 顏色設定
    COLORS = {
        'title': (70, 130, 180),  # 鋼藍色
        'subtitle': (200, 200, 200),
        'button': (70, 130, 180),
        'button_hover': (100, 160, 210),
        'button_text': (255, 255, 255),
        'button_shadow': (30, 60, 90)
    }
    
    # 標題
    title = title_font.render(title_text, True, COLORS['title'])
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    
    # 副標題（如果有）
    subtitle = None
    subtitle_rect = None
    if subtitle_text:
        subtitle = subtitle_font.render(subtitle_text, True, COLORS['subtitle'])
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
    
    # 版本資訊（如果有）
    version = None
    version_rect = None
    if version_text:
        version = subtitle_font.render(version_text, True, COLORS['subtitle'])
        version_rect = version.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
    
    # 初始化星星位置（帶亮度變化）
    stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(100, 255)) for _ in range(50)]
    
    # 創建漸層背景
    gradient_bg = create_gradient_background(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # 載入背景圖片（如果提供）
    bg_surface = None
    if background_image:
        try:
            bg_surface = pygame.image.load(background_image).convert()
            bg_surface = pygame.transform.scale(bg_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            bg_surface = None
    
    # 按鈕設定
    button_width, button_height = 200, 50
    button_padding = 20
    for i, btn in enumerate(buttons):
        btn['rect'] = pygame.Rect(0, 0, button_width, button_height)
        btn['rect'].center = (SCREEN_WIDTH // 2, 300 + i * (button_height + button_padding))
        btn['text_surface'] = button_font.render(btn['text'], True, COLORS['button_text'])
        btn['text_rect'] = btn['text_surface'].get_rect(center=btn['rect'].center)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                mouse_clicked = True
            if allow_esc_resume and event.type == KEYDOWN and event.key == K_ESCAPE:
                return "resume"  # 僅對暫停畫面有效
        
        # 繪製背景
        if bg_surface:
            screen.blit(bg_surface, (0, 0))
        else:
            screen.blit(gradient_bg, (0, 0))
            # 繪製星星
            for x, y, brightness in stars:
                color = (brightness, brightness, brightness)
                pygame.draw.circle(screen, color, (x, y), 1)
                # 更新亮度
                stars[stars.index((x, y, brightness))] = (x, y, (brightness + random.randint(-5, 5)) % 255)
        
        # 繪製標題
        screen.blit(title, title_rect)
        
        # 繪製副標題（如果有）
        if subtitle:
            screen.blit(subtitle, subtitle_rect)
        
        # 繪製版本資訊（如果有）
        if version:
            screen.blit(version, version_rect)
        
        # 繪製按鈕
        for btn in buttons:
            button_color = COLORS['button_hover'] if btn['rect'].collidepoint(mouse_pos) else COLORS['button']
            pygame.draw.rect(screen, COLORS['button_shadow'], btn['rect'].move(3, 3))
            pygame.draw.rect(screen, button_color, btn['rect'], border_radius=10)
            pygame.draw.rect(screen, BLACK, btn['rect'], 2, border_radius=10)
            screen.blit(btn['text_surface'], btn['text_rect'])
            
            if mouse_clicked and btn['rect'].collidepoint(mouse_pos):
                return btn['action']
        
        pygame.display.flip()
        clock.tick(FPS)

# === 開始畫面 ===
def start_screen(screen):
    buttons = [
        {"text": "開始遊戲", "action": "start"}, 
        {"text": "離開遊戲", "action": "quit"}
    ]
    return menu_screen(
        screen,
        title_text="太空戰機 Quiz",
        buttons=buttons,
        subtitle_text="知識大挑戰",
        version_text="v1.0.0",
        background_image="pic/menu_bg.png"
    )

# === 暫停畫面 ===
def pause_screen(screen):
    buttons = [
        {"text": "繼續遊戲", "action": "resume"},
        {"text": "返回主選單", "action": "menu"},
        {"text": "退出遊戲", "action": "quit"}
    ]
    return menu_screen(
        screen,
        title_text="遊戲暫停",
        buttons=buttons,
        allow_esc_resume=True
    )

# === 遊戲結束畫面 ===
def game_over_screen(screen):
    buttons = [
        {"text": "回到主選單", "action": "menu"},
        {"text": "結束遊戲", "action": "quit"}
    ]
    return menu_screen(
        screen,
        title_text="你已經陣亡",
        buttons=buttons
    )

# === 主遊戲迴圈 ===
def run_game(screen, images, sounds, questions, font):
    clock = pygame.time.Clock()
    game_state = GameState()
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    rocks = pygame.sprite.Group()
    monsters = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()
    items = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    player = Player(images['plane'], SCREEN_WIDTH, SCREEN_HEIGHT)
    all_sprites.add(player)
    
    paused = False
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    paused = not paused
                elif event.key == K_l and game_state.special:  # 按 L 觸發雷射
                    laser = LaserBeam(player.rect.centerx, player.rect.centery)
                    all_sprites.add(laser)
                    lasers.add(laser)
                    game_state.special = False  # 重置特殊狀態
                    game_state.special_cooldown = SPECIAL_COOLDOWN_FRAMES  # 設置冷卻
                    if sounds['shoot']:
                        sounds['shoot'].play()
        
        if paused:
            action = pause_screen(screen)
            if action == "resume":
                paused = False
            elif action == "menu":
                return "menu"
            elif action == "quit":
                pygame.quit()
                sys.exit()
            clock.tick(FPS)
            continue
        
        # 更新特殊武器冷卻
        if game_state.special_cooldown > 0:
            game_state.special_cooldown -= 1
            if game_state.special_cooldown == 0:
                game_state.special = True  # 冷卻結束後恢復 special
        
        # 生成物件
        spawn_objects(game_state, all_sprites, items, monsters, rocks, boss_group, images, game_state.level, enemy_bullets, sounds)
        
        # 更新玩家和所有精靈
        keys = pygame.key.get_pressed()
        all_sprites.update({'left': K_LEFT, 'right': K_RIGHT})
        
        # 處理物品撿取
        handle_item_collisions(player, items, game_state, screen, font, questions, all_sprites, rocks, monsters, enemy_bullets, particles, sounds['explosion'])
        
        # 處理玩家射擊
        handle_player_shooting(player, keys, game_state, all_sprites, bullets, lasers, images['bullet'], sounds['shoot'], monsters)
        
        # 處理碰撞
        collision_result = handle_collisions(player, bullets, lasers, rocks, monsters, enemy_bullets, particles, all_sprites, game_state, sounds['explosion'], boss_group)
        if collision_result == "game_over":
            action = game_over_screen(screen)
            if action == "menu":
                return "menu"
            elif action == "quit":
                pygame.quit()
                sys.exit()
        elif collision_result:
            break
        
        # 更新等級
        update_level(game_state)
        
        # 繪製
        screen.blit(images['background'], (0, 0))
        for b in bullets:
            if hasattr(b, 'track') and b.track:
                if not hasattr(b, 'trail'):
                    b.trail = []
                b.trail.append(b.rect.center)
                if len(b.trail) > 10:
                    b.trail.pop(0)
                for i, pos in enumerate(b.trail):
                    alpha = 255 * (1 - i / len(b.trail))
                    pygame.draw.circle(screen, (0, 0, 255, int(alpha)), pos, 3)
        all_sprites.draw(screen)
        particles.draw(screen)
        
        # 繪製血條
        for e in list(rocks) + list(monsters):
            if hasattr(e, 'health'):
                bar_w, bar_h = e.rect.width, 5
                frac = e.health / e.max_health
                pygame.draw.rect(screen, RED, (e.rect.x, e.rect.y - 10, bar_w * frac, bar_h))
                pygame.draw.rect(screen, WHITE, (e.rect.x, e.rect.y - 10, bar_w, bar_h), 1)
        
        # 繪製 UI
        draw_ui(screen, game_state.score, player, game_state.level, game_state.high_score, game_state.special)
        pygame.display.flip()
        clock.tick(FPS)
# === 主程式 ===
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('太空戰機 Quiz')
    
    # 載入資源
    images = {
        'plane': load_image('pic/plane.png', (50, 50), 'plane'),
        'bullet': load_image('pic/bullet.png', (5, 15), 'bullet'),
        'rock': load_image('pic/rock.png', (40, 40), 'rock'),
        'monster': load_image('pic/monster.png', (50, 50), 'rock'),
        'boss': load_image('pic/boss4.png', (100, 80), 'plane'),
        'life': load_image('pic/life.png', (30, 30), 'item'),
        'weapon': load_image('pic/weapon.png', (30, 30), 'item'),
        'quiz': load_image('pic/history_book.png', (30, 30), 'item'),
        'enemy_bullet': load_image('pic/enemy_bullet.png', (10, 20), 'bullet'),
        'background': load_image('pic/background.png', (SCREEN_WIDTH, SCREEN_HEIGHT), 'item')
    }
    sounds = {
        'shoot': pygame.mixer.Sound('sound/shoot.wav') if pygame.mixer.get_init() else None,
        'explosion': pygame.mixer.Sound('sound/explosion.wav') if pygame.mixer.get_init() else None
    }
    questions = load_historical_questions_from_excel()
    font = pygame.font.SysFont('Microsoft JhengHei', 36)
    
    while True:
        result = start_screen(screen)
        if result == "quit":
            pygame.quit()
            sys.exit()
        elif result == "start":
            result = run_game(screen, images, sounds, questions, font)
            if result == "menu":
                continue
            break
        
if __name__=='__main__':
    main()
