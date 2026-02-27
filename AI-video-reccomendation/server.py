import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import logging
import random
import math
import uuid
import time
import hashlib
import numpy as np
import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.dirname(__file__))
from generation import GenerationPipeline, InterestProfiler
from generation.config import GenerationConfig

app = Flask(__name__)
CORS(app)

VIDEOS_DIR = os.path.join(os.getcwd(), "videos")
EMBEDDING_DIM = 512
ALPHA = 0.1

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
backbone = torch.nn.Sequential(*list(resnet.children())[:-1])
backbone = backbone.to(device)
backbone.eval()

img_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ---------------------------------------------------------------------------
# Data stores (in-memory)
# ---------------------------------------------------------------------------

auth_tokens = {}  # token -> user_id

users_db = {}  # user_id -> User dict

videos_db = {}  # video_id -> Video dict

comments_db = defaultdict(list)  # video_id -> [Comment]

interaction_log = []  # [{user_id, video_id, type, value, timestamp}]

user_item_matrix = defaultdict(lambda: defaultdict(float))  # user_id -> {video_id -> score}

CATEGORIES = [
    "Nature", "Urban", "Abstract", "Architecture", "Cinematic",
    "Landscape", "Animals", "Weather", "Ocean", "Space",
    "Technology", "Art", "Music", "Dance", "Comedy",
    "Travel", "Food", "Fitness", "Fashion", "DIY",
    "Education", "Gaming", "Pets", "ASMR", "Satisfying",
    "Fractal", "Generative", "Gradient", "Retro", "Psychedelic",
]

MUSIC_TRACKS = [
    {"name": "Original Sound", "artist": "creator"},
    {"name": "Blinding Lights", "artist": "The Weeknd"},
    {"name": "Levitating", "artist": "Dua Lipa"},
    {"name": "Stay", "artist": "Kid LAROI & Justin Bieber"},
    {"name": "Heat Waves", "artist": "Glass Animals"},
    {"name": "Peaches", "artist": "Justin Bieber"},
    {"name": "Montero", "artist": "Lil Nas X"},
    {"name": "Good 4 U", "artist": "Olivia Rodrigo"},
    {"name": "Kiss Me More", "artist": "Doja Cat"},
    {"name": "Butter", "artist": "BTS"},
    {"name": "Astronaut In The Ocean", "artist": "Masked Wolf"},
    {"name": "Save Your Tears", "artist": "The Weeknd"},
    {"name": "drivers license", "artist": "Olivia Rodrigo"},
    {"name": "Watermelon Sugar", "artist": "Harry Styles"},
    {"name": "Mood", "artist": "24kGoldn"},
    {"name": "positions", "artist": "Ariana Grande"},
    {"name": "Dynamite", "artist": "BTS"},
    {"name": "Savage Love", "artist": "Jason Derulo"},
    {"name": "Roses (Imanbek Remix)", "artist": "SAINt JHN"},
    {"name": "Blinding Lights (Remix)", "artist": "The Weeknd"},
    {"name": "Sunflower", "artist": "Post Malone"},
    {"name": "Old Town Road", "artist": "Lil Nas X"},
    {"name": "bad guy", "artist": "Billie Eilish"},
    {"name": "Don't Start Now", "artist": "Dua Lipa"},
    {"name": "Circles", "artist": "Post Malone"},
    {"name": "Roxanne", "artist": "Arizona Zervas"},
    {"name": "Adore You", "artist": "Harry Styles"},
    {"name": "Intentions", "artist": "Justin Bieber"},
    {"name": "Say So", "artist": "Doja Cat"},
    {"name": "HIGHEST IN THE ROOM", "artist": "Travis Scott"},
    {"name": "someone you loved", "artist": "Lewis Capaldi"},
    {"name": "Falling", "artist": "Trevor Daniel"},
    {"name": "Toosie Slide", "artist": "Drake"},
    {"name": "Motivation", "artist": "Normani"},
    {"name": "Therefore I Am", "artist": "Billie Eilish"},
    {"name": "Laugh Now Cry Later", "artist": "Drake"},
    {"name": "Rockstar", "artist": "DaBaby"},
    {"name": "INDUSTRY BABY", "artist": "Lil Nas X"},
    {"name": "Shivers", "artist": "Ed Sheeran"},
    {"name": "STAY", "artist": "The Kid LAROI"},
]

FAKE_USERNAMES = [
    "alex_creates", "maya.films", "urban.lens", "nature_vibes",
    "cinematic.soul", "pixel.artist", "wave.rider", "sky.chaser",
    "neon.nights", "wild.frames", "dream.catcher", "echo.visual",
    "storm.clips", "golden.hour", "deep.focus", "flow.state",
    "vibe.check", "mood.board", "raw.footage", "frame.by.frame",
    "aesthetic.edits", "luna.clips", "solar.films", "midnight.reel",
    "velvet.lens", "cosmic.shots", "crystal.clear", "ember.glow",
    "frost.bite", "jade.visuals", "karma.content", "lush.life",
    "marble.media", "nova.edits", "opal.studio", "prism.views",
    "quartz.films", "ruby.reels", "sage.cinema", "terra.shots",
    "ultra.vibe", "violet.haze", "winter.mood", "xeno.art",
    "zen.captures", "amber.tones", "blaze.clips", "cedar.lens",
    "dusk.films", "eden.visuals", "fern.frames", "glow.reel",
    "haze.studio", "iris.content", "jasper.media", "koi.captures",
    "lapis.films", "mist.visuals", "nimbus.art", "onyx.edits",
    "pearl.lens", "quill.studio", "rain.drops", "stellar.shots",
    "tide.media", "umbra.films", "vale.visuals", "wren.clips",
    "yonder.lens", "zephyr.art", "ash.creates", "birch.films",
    "coral.media", "drift.studio", "elm.visuals", "fjord.lens",
    "grove.shots", "hazel.clips", "indigo.reel", "juniper.art",
    "kelp.media", "lotus.films", "moss.studio", "nectar.lens",
    "orchid.art", "pine.visuals", "reef.clips", "stone.media",
    "thistle.art", "tundra.films", "vine.studio", "willow.lens",
    "aurora.shots", "breeze.clips", "canyon.media", "delta.films",
    "equinox.art", "flame.studio", "glacier.lens", "harbor.shots",
    "isle.clips", "jetstream.art",
]

COMMENT_TEMPLATES = [
    "this is incredible! 🔥", "wow the cinematography 😍", "obsessed with this",
    "how do you make these??", "literally perfect", "the vibes are immaculate ✨",
    "this should have more views", "adding this to my favorites",
    "the colors in this 🎨", "i could watch this on loop forever",
    "this is art", "goosebumps", "underrated content fr",
    "the lighting tho 👀", "main character energy", "aesthetic overload",
    "this hits different at 3am", "saving this for later", "chef's kiss 🤌",
    "nah this is too good", "POV: you found the best creator",
    "tutorial when??", "the transition 😩🔥", "living for this content",
    "why isn't this viral yet", "absolutely stunning", "crying this is so beautiful",
    "this is exactly what my fyp needed", "legend", "pure talent 🙌",
    "the way this makes me feel 🥺", "i need more of this content",
    "new favorite creator tbh", "showed this to everyone i know",
    "the detail in this is insane", "how is this not on my fyp more",
    "literally screaming 😭", "this unlocked a core memory",
    "the algorithm finally did something right", "inject this into my veins",
    "bro this is CINEMA", "im not okay after watching this",
    "rent free in my head now", "this is what the internet was made for",
    "my jaw literally dropped", "ok but the QUALITY",
    "the talent jumped out", "this deserves an award fr",
    "crying in the club rn 😭", "never skip this on my fyp",
    "peak content right here", "the vibe is unmatched ✨",
    "i felt this in my soul", "alexa play this on repeat",
    "whoever made this needs a raise", "this is giving everything",
    "not me watching this 50 times", "the aesthetic is *chefs kiss*",
    "dropped my phone watching this", "this cured my depression ngl",
    "taking notes fr fr 📝", "wish i could double like",
    "my fyp has taste today", "this is so calming omg",
    "the creativity here is unmatched", "ok now THIS is content",
    "straight to my saved folder", "i gasped", "no thoughts just vibes",
    "the color grading tho 🎨", "masterclass in editing",
    "society if everyone made content like this", "W creator",
    "this just healed something in me", "the precision 🎯",
    "god tier content", "i will never recover from this",
]

DESCRIPTIONS = [
    "wait for it... #fyp #viral", "POV: you discovered something beautiful #aesthetic",
    "this took 3 hours to film 😅 #filmmaker", "nature never disappoints 🌿 #nature",
    "caught in 4k 📸 #cinematic", "the golden hour hits different #goldenhour",
    "no filter needed #raw #real", "when the light is perfect ✨",
    "exploring hidden gems #explore #travel", "this view tho 😍 #views",
    "moody vibes only #mood #aesthetic", "urban jungle 🏙️ #city #urban",
    "art in motion #art #creative", "just vibes #chill #relax",
    "another day another masterpiece #content", "the beauty in details #macro",
    "chasing light 🌅 #photography", "found this spot by accident #hidden",
    "can't stop watching this #loop #satisfying", "reality is beautiful #nofilter",
    "ocean therapy 🌊 #ocean #waves #peaceful", "fractal universe 🌌 #math #art",
    "when math becomes art #fractal #generative", "living colors #gradient #abstract",
    "cellular automata are mesmerizing #science", "matrix vibes 💚 #tech #code",
    "lost in the waves 🌊 #beach #sunset", "fire & ice 🔥❄️ #contrast",
    "this pattern is hypnotic #satisfying", "infinite zoom #mandelbrot #fractal",
    "nature's algorithm 🧬 #pattern #organic", "neon dreams #neon #nightlife",
    "slow motion magic #slowmo #cinematic", "abstract reality #abstract #art",
    "chasing storms ⛈️ #weather #nature", "underwater world 🐠 #ocean #diving",
    "city never sleeps 🌃 #nightlife #urban", "pure geometry #pattern #minimal",
    "this sunset was unreal 🌅 #sunset", "smoke & mirrors 💨 #artistic",
    "retro vibes only 📺 #retro #vintage", "psychedelic journey 🍄 #trippy",
    "forest bathing 🌲 #forest #zen", "the algorithm blessed me today #fyp",
    "aerial perspective 🚁 #drone #aerial", "cozy content ☕ #cozy #comfort",
    "winter wonderland ❄️ #snow #winter", "spring awakening 🌸 #spring #bloom",
    "summer energy ☀️ #summer #vibes", "autumn feels 🍂 #fall #autumn",
    "midnight thoughts 🌙 #night #mood", "dawn patrol 🌅 #sunrise #morning",
    "visual ASMR #asmr #satisfying #calm", "generative art is the future #ai #art",
    "the universe is math 🔢 #science", "color theory in action 🎨 #design",
]

# ---------------------------------------------------------------------------
# Embedding extraction (ResNet-18)
# ---------------------------------------------------------------------------

def extract_frame_embeddings(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return np.zeros((1, EMBEDDING_DIM))
    frame_embeddings = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_indices = np.linspace(0, max(frame_count - 1, 0), min(8, frame_count), dtype=int)
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        tensor = img_transform(frame).unsqueeze(0).to(device)
        with torch.no_grad():
            emb = backbone(tensor).squeeze().cpu().numpy()
            if emb.ndim > 1:
                emb = emb.reshape(-1)
            frame_embeddings.append(emb)
    cap.release()
    if not frame_embeddings:
        return np.zeros((1, EMBEDDING_DIM))
    return np.array(frame_embeddings)


def get_video_embedding(video_id):
    v = videos_db.get(video_id)
    if not v:
        return np.zeros(EMBEDDING_DIM)
    if v['embedding'] is None:
        video_path = os.path.join(VIDEOS_DIR, v['filename'])
        if os.path.exists(video_path):
            frames = extract_frame_embeddings(video_path)
            v['embedding'] = np.mean(frames, axis=0)
        else:
            v['embedding'] = np.zeros(EMBEDDING_DIM)
    return v['embedding']


def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 10.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return max(frames / fps, 1.0)


# ---------------------------------------------------------------------------
# Monolith Recommendation Engine
# ---------------------------------------------------------------------------

class CollisionlessEmbeddingTable:
    """Hash-map based embedding storage with no collisions (unlike feature-hashing approaches)."""
    def __init__(self, dim):
        self.dim = dim
        self.table = {}

    def get(self, key):
        if key not in self.table:
            self.table[key] = np.random.randn(self.dim) * 0.01
        return self.table[key]

    def set(self, key, value):
        self.table[key] = value

    def update(self, key, gradient, lr=0.01):
        current = self.get(key)
        self.table[key] = current + lr * gradient


class MonolithRecommender:
    """
    Inspired by ByteDance's Monolith system.
    Single unified model for candidate generation + ranking with real-time updates.
    Features: collisionless embedding tables, multi-signal scoring, diversity re-ranking.
    """
    def __init__(self):
        self.user_embeddings = CollisionlessEmbeddingTable(EMBEDDING_DIM)
        self.user_interest_embeddings = CollisionlessEmbeddingTable(64)
        self.scoring_weights = {
            'content_similarity': 0.25,
            'collaborative': 0.20,
            'engagement_quality': 0.15,
            'freshness': 0.08,
            'creator_affinity': 0.10,
            'category_interest': 0.12,
            'completion_prediction': 0.05,
            'exploration_bonus': 0.05,
        }

    def get_recommendations(self, user_id, n=5, feed_type='foryou'):
        user = users_db.get(user_id)
        if not user:
            return self._cold_start_recommendations(n)

        watched = set(user.get('watched_videos', []))

        if feed_type == 'following':
            return self._following_feed(user_id, watched, n)

        candidates = self._generate_candidates(user_id, watched, n * 5)
        scored = self._score_candidates(user_id, candidates)
        diverse = self._diversity_rerank(scored, n)
        final = self._inject_exploration(user_id, diverse, watched, n)
        return final

    def _cold_start_recommendations(self, n):
        all_videos = list(videos_db.keys())
        trending = sorted(all_videos, key=lambda vid: videos_db[vid]['stats']['engagement_score'], reverse=True)
        selected = trending[:n * 2]
        random.shuffle(selected)
        return [self._build_video_response(vid) for vid in selected[:n]]

    def _following_feed(self, user_id, watched, n):
        user = users_db[user_id]
        following = set(user.get('following', []))
        if not following:
            return self._cold_start_recommendations(n)
        candidates = []
        for vid, v in videos_db.items():
            if vid in watched:
                continue
            if v['creator_id'] in following:
                candidates.append(vid)
        candidates.sort(key=lambda vid: videos_db[vid]['created_at'], reverse=True)
        return [self._build_video_response(vid) for vid in candidates[:n]]

    def _generate_candidates(self, user_id, watched, n):
        content_based = self._content_based_candidates(user_id, watched, n // 3)
        collaborative = self._collaborative_candidates(user_id, watched, n // 3)
        trending = self._trending_candidates(watched, n // 3)
        all_candidates = {}
        for vid, scores in content_based:
            all_candidates[vid] = scores
        for vid, scores in collaborative:
            if vid in all_candidates:
                all_candidates[vid].update(scores)
            else:
                all_candidates[vid] = scores
        for vid, scores in trending:
            if vid in all_candidates:
                all_candidates[vid].update(scores)
            else:
                all_candidates[vid] = scores
        return all_candidates

    def _content_based_candidates(self, user_id, watched, n):
        user_emb = self.user_embeddings.get(user_id).reshape(1, -1)
        candidates = []
        for vid, v in videos_db.items():
            if vid in watched:
                continue
            emb = get_video_embedding(vid)
            if emb is None:
                continue
            sim = cosine_similarity(user_emb, emb.reshape(1, -1))[0][0]
            candidates.append((vid, {'content_similarity': float(sim)}))
        candidates.sort(key=lambda x: x[1]['content_similarity'], reverse=True)
        return candidates[:n]

    def _collaborative_candidates(self, user_id, watched, n):
        user_likes = set()
        for vid, v in videos_db.items():
            if user_id in v.get('liked_by', set()):
                user_likes.add(vid)
        if not user_likes:
            return []
        similar_users = []
        for uid in users_db:
            if uid == user_id:
                continue
            their_likes = set()
            for vid, v in videos_db.items():
                if uid in v.get('liked_by', set()):
                    their_likes.add(vid)
            if not their_likes:
                continue
            overlap = len(user_likes & their_likes)
            union = len(user_likes | their_likes)
            if union > 0:
                jaccard = overlap / union
                if jaccard > 0.05:
                    similar_users.append((uid, jaccard))
        similar_users.sort(key=lambda x: x[1], reverse=True)
        similar_users = similar_users[:10]
        candidate_scores = defaultdict(float)
        for uid, sim in similar_users:
            for vid, v in videos_db.items():
                if vid in watched or vid in user_likes:
                    continue
                if uid in v.get('liked_by', set()):
                    candidate_scores[vid] += sim
        candidates = [(vid, {'collaborative': score})
                      for vid, score in candidate_scores.items()]
        candidates.sort(key=lambda x: x[1]['collaborative'], reverse=True)
        return candidates[:n]

    def _trending_candidates(self, watched, n):
        now = time.time()
        candidates = []
        for vid, v in videos_db.items():
            if vid in watched:
                continue
            age_hours = (now - v['created_at']) / 3600
            decay = math.exp(-0.01 * age_hours)
            trending_score = v['stats']['engagement_score'] * decay
            candidates.append((vid, {'trending': trending_score}))
        candidates.sort(key=lambda x: x[1]['trending'], reverse=True)
        return candidates[:n]

    def _score_candidates(self, user_id, candidates):
        user = users_db.get(user_id, {})
        user_interests = user.get('category_interests', {})
        user_following = set(user.get('following', []))
        scored = []
        for vid, signals in candidates.items():
            v = videos_db[vid]
            content_sim = signals.get('content_similarity', 0)
            collab = signals.get('collaborative', 0)
            trending = signals.get('trending', 0)

            age_hours = (time.time() - v['created_at']) / 3600
            freshness = math.exp(-0.005 * age_hours)

            creator_affinity = 0.5 if v['creator_id'] in user_following else 0
            for liked_creator in self._get_liked_creators(user_id):
                if v['creator_id'] == liked_creator:
                    creator_affinity = max(creator_affinity, 0.8)

            cat = v.get('category', 'Unknown')
            cat_interest = user_interests.get(cat, 0)
            max_interest = max(user_interests.values()) if user_interests else 1
            cat_interest = cat_interest / max(max_interest, 1)

            stats = v['stats']
            completion = stats.get('avg_completion_rate', 0.5)

            score = (
                self.scoring_weights['content_similarity'] * max(content_sim, 0) +
                self.scoring_weights['collaborative'] * min(collab, 1) +
                self.scoring_weights['engagement_quality'] * min(trending, 1) +
                self.scoring_weights['freshness'] * freshness +
                self.scoring_weights['creator_affinity'] * creator_affinity +
                self.scoring_weights['category_interest'] * cat_interest +
                self.scoring_weights['completion_prediction'] * completion +
                self.scoring_weights['exploration_bonus'] * random.uniform(0, 0.3)
            )
            scored.append({
                'video_id': vid,
                'score': score,
                'signals': signals,
                'category': cat
            })
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored

    def _diversity_rerank(self, scored, n):
        """Maximal Marginal Relevance for diversity."""
        if len(scored) <= n:
            return [s['video_id'] for s in scored]
        selected = [scored[0]]
        remaining = scored[1:]
        while len(selected) < n and remaining:
            best_idx = 0
            best_mmr = -float('inf')
            for i, candidate in enumerate(remaining):
                relevance = candidate['score']
                max_sim = 0
                for s in selected:
                    if candidate['category'] == s['category']:
                        max_sim = max(max_sim, 0.5)
                    if videos_db[candidate['video_id']]['creator_id'] == videos_db[s['video_id']]['creator_id']:
                        max_sim = max(max_sim, 0.7)
                lam = 0.6
                mmr = lam * relevance - (1 - lam) * max_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = i
            selected.append(remaining.pop(best_idx))
        return [s['video_id'] for s in selected]

    def _inject_exploration(self, user_id, ranked_ids, watched, n):
        exploration_rate = 0.15
        num_explore = max(1, int(n * exploration_rate))
        all_unwatched = [vid for vid in videos_db if vid not in watched and vid not in ranked_ids]
        if all_unwatched:
            explore_vids = random.sample(all_unwatched, min(num_explore, len(all_unwatched)))
            insert_positions = sorted(random.sample(range(1, min(n, len(ranked_ids) + 1)),
                                                     min(num_explore, len(ranked_ids))))
            for pos, vid in zip(insert_positions, explore_vids):
                ranked_ids.insert(pos, vid)
        return [self._build_video_response(vid) for vid in ranked_ids[:n]]

    def _build_video_response(self, vid):
        v = videos_db.get(vid)
        if not v:
            return None
        return {
            'video_id': vid,
            'filename': v['filename'],
            'url': f"/videos/{v['filename']}",
            'creator': {
                'user_id': v['creator_id'],
                'username': users_db.get(v['creator_id'], {}).get('username', 'unknown'),
                'display_name': users_db.get(v['creator_id'], {}).get('display_name', 'Unknown'),
                'avatar': users_db.get(v['creator_id'], {}).get('avatar', ''),
                'is_verified': users_db.get(v['creator_id'], {}).get('is_verified', False),
            },
            'description': v.get('description', ''),
            'music': v.get('music', {'name': 'Original Sound', 'artist': 'creator'}),
            'category': v.get('category', 'Unknown'),
            'tags': v.get('tags', []),
            'stats': {
                'views': v['stats']['views'],
                'likes': v['stats']['likes'],
                'comments': v['stats']['comment_count'],
                'shares': v['stats']['shares'],
            },
            'duration': v.get('duration', 10),
            'created_at': v['created_at'],
        }

    def _get_liked_creators(self, user_id):
        creators = set()
        for vid, v in videos_db.items():
            if user_id in v.get('liked_by', set()):
                creators.add(v['creator_id'])
        return creators

    def update_user_embedding(self, user_id, video_id, interaction_type, value=1.0):
        video_emb = get_video_embedding(video_id)
        user_emb = self.user_embeddings.get(user_id)
        weights = {'like': 0.3, 'comment': 0.25, 'share': 0.35, 'watch_time': 0.1, 'view': 0.02}
        w = weights.get(interaction_type, 0.05) * value
        gradient = w * (video_emb - user_emb)
        self.user_embeddings.update(user_id, gradient, lr=ALPHA)
        v = videos_db.get(video_id)
        if v:
            cat = v.get('category', 'Unknown')
            user = users_db.get(user_id)
            if user:
                interests = user.setdefault('category_interests', {})
                boost = {'like': 2.0, 'comment': 1.5, 'share': 2.5, 'watch_time': value * 0.5, 'view': 0.2}
                interests[cat] = interests.get(cat, 0) + boost.get(interaction_type, 0.1)
        user_item_matrix[user_id][video_id] += w


recommender = MonolithRecommender()

gen_config = GenerationConfig(
    enabled=True,
    provider="stub",
    generated_content_ratio=0.15,
    num_user_clusters=8,
    cluster_pool_target=10,
    budget_per_cluster_per_hour=5,
)
gen_pipeline = GenerationPipeline(gen_config, VIDEOS_DIR)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def generate_avatar_url(username):
    h = hashlib.md5(username.encode()).hexdigest()
    return f"https://api.dicebear.com/7.x/avataaars/svg?seed={h}"


BIOS = [
    "creating cool stuff ✨", "filmmaker 🎬", "visual storyteller",
    "capturing moments 📸", "just vibes 🌊", "art is life 🎨",
    "exploring the world 🌍", "content creator", "dreamer & creator",
    "digital artist 🖥️", "chasing sunsets 🌅", "nature lover 🌿",
    "abstract thinker 🧠", "night owl 🦉", "coffee & creativity ☕",
    "fractal enthusiast 🔮", "generative art nerd", "pixel perfectionist",
    "ocean soul 🐚", "mountain life ⛰️", "urban explorer 🏙️",
    "ambient vibes 🎧", "analog in a digital world", "color theory addict",
    "shooting in raw 📷", "golden hour chaser", "moody aesthetics",
    "creative director", "self-taught everything", "less is more",
    "making things beautiful", "visual poet", "light painter 💡",
    "minimalist maximizer", "wanderlust 🗺️", "storm chaser ⛈️",
    "deep sea explorer 🤿", "aerial perspective 🚁", "macro world 🔬",
    "retro futurist", "vaporwave is not dead", "synthwave lover 🌆",
]

VIDEO_CATEGORY_MAP = {
    'pexels_ocean': 'Ocean', 'pexels_sunset': 'Landscape', 'pexels_city': 'Urban',
    'pexels_forest': 'Nature', 'pexels_rain': 'Weather', 'pexels_clouds': 'Weather',
    'pexels_neon': 'Urban', 'pexels_waterfall': 'Nature', 'pexels_highway': 'Urban',
    'pexels_fireworks': 'Cinematic', 'pexels_snow': 'Weather', 'pexels_flower': 'Nature',
    'pexels_bird': 'Animals', 'pexels_waves': 'Ocean', 'pexels_starry': 'Space',
    'pexels_autumn': 'Nature', 'pexels_lightning': 'Weather', 'pexels_underwater': 'Ocean',
    'pexels_coffee': 'Food', 'pexels_train': 'Travel', 'pexels_morning': 'Landscape',
    'pexels_dandelion': 'Nature', 'pexels_jellyfish': 'Ocean', 'pexels_campfire': 'Nature',
    'pexels_palm': 'Travel', 'pexels_traffic': 'Urban', 'pexels_galaxy': 'Space',
    'pexels_butterfly': 'Animals', 'pexels_drone': 'Landscape', 'pexels_northern': 'Nature',
    'pexels_beach': 'Ocean', 'pexels_road': 'Travel', 'pexels_cat': 'Pets',
    'pexels_bokeh': 'Abstract', 'pexels_river': 'Nature', 'pexels_night': 'Urban',
    'pexels_wave_crash': 'Ocean', 'pexels_field': 'Landscape', 'pexels_smoke': 'Abstract',
    'pexels_cooking': 'Food', 'pexels_timelapse': 'Cinematic',
    'gen_mandelbrot': 'Fractal', 'gen_life': 'Generative', 'gen_cellauto': 'Generative',
    'gen_gradient': 'Gradient', 'gen_noise': 'Abstract', 'gen_color_pulse': 'Abstract',
    'gen_plasma': 'Psychedelic', 'gen_wave': 'Abstract', 'gen_sierpinski': 'Fractal',
    'gen_testsrc': 'Retro', 'gen_radial': 'Abstract', 'gen_moire': 'Satisfying',
    'gen_tunnel': 'Psychedelic', 'gen_spiral': 'Psychedelic', 'gen_fire': 'Abstract',
    'gen_matrix': 'Technology', 'gen_psychedelic': 'Psychedelic',
    'gen_extra': 'Generative', 'gen_checkerboard': 'Satisfying', 'gen_lissajous': 'Abstract',
}

def _classify_video(filename):
    name = os.path.splitext(filename)[0].lower()
    for prefix, cat in VIDEO_CATEGORY_MAP.items():
        if name.startswith(prefix):
            return cat
    return random.choice(CATEGORIES)


def seed_data():
    random.seed(42)
    np.random.seed(42)
    num_users = len(FAKE_USERNAMES)

    for i, uname in enumerate(FAKE_USERNAMES):
        uid = f"user_{i}"
        users_db[uid] = {
            'user_id': uid,
            'username': uname,
            'display_name': uname.replace('.', ' ').replace('_', ' ').title(),
            'avatar': generate_avatar_url(uname),
            'bio': BIOS[i % len(BIOS)],
            'followers': [],
            'following': [],
            'follower_count': 0,
            'following_count': 0,
            'liked_videos': [],
            'watched_videos': [],
            'category_interests': {},
            'is_verified': i < 15,
            'total_likes': random.randint(0, 50000),
            'created_at': time.time() - random.randint(86400 * 30, 86400 * 365),
        }

    for i in range(num_users):
        uid = f"user_{i}"
        num_following = random.randint(3, min(25, num_users - 1))
        possible = [f"user_{j}" for j in range(num_users) if j != i]
        following = random.sample(possible, min(num_following, len(possible)))
        users_db[uid]['following'] = following
        users_db[uid]['following_count'] = len(following)
        for fid in following:
            users_db[fid]['followers'].append(uid)
            users_db[fid]['follower_count'] = len(users_db[fid]['followers'])

    if not os.path.exists(VIDEOS_DIR):
        return

    video_files = sorted([f for f in os.listdir(VIDEOS_DIR) if f.endswith(('.mp4', '.mov')) and f != 'demo.mov'])
    for i, filename in enumerate(video_files):
        vid = os.path.splitext(filename)[0]
        creator_id = f"user_{i % num_users}"
        category = _classify_video(filename)
        music = MUSIC_TRACKS[i % len(MUSIC_TRACKS)]
        description = DESCRIPTIONS[i % len(DESCRIPTIONS)]
        tags = [f"#{category.lower()}", "#fyp", "#viral",
                f"#{random.choice(['aesthetic', 'cinematic', 'art', 'creative', 'mood', 'satisfying', 'trending', 'explore'])}",
                f"#{random.choice(['foryou', 'discover', 'trending', 'hot'])}"]
        video_path = os.path.join(VIDEOS_DIR, filename)
        duration = get_video_duration(video_path)

        is_viral = random.random() < 0.15
        if is_viral:
            base_views = random.randint(500000, 5000000)
        else:
            base_views = random.randint(500, 500000)
        base_likes = int(base_views * random.uniform(0.03, 0.30))
        base_comments = int(base_likes * random.uniform(0.03, 0.20))
        base_shares = int(base_likes * random.uniform(0.01, 0.10))
        engagement_score = (base_likes * 2 + base_comments * 3 + base_shares * 5) / max(base_views, 1)

        videos_db[vid] = {
            'video_id': vid,
            'filename': filename,
            'embedding': None,
            'creator_id': creator_id,
            'description': description,
            'music': music,
            'category': category,
            'tags': tags,
            'duration': duration,
            'created_at': time.time() - random.randint(3600, 86400 * 30),
            'liked_by': set(),
            'stats': {
                'views': base_views,
                'likes': base_likes,
                'comment_count': base_comments,
                'shares': base_shares,
                'engagement_score': engagement_score,
                'total_watch_time': 0,
                'watch_count': 0,
                'avg_completion_rate': random.uniform(0.3, 0.95),
            }
        }

        num_comments = random.randint(5, 25)
        for _ in range(num_comments):
            commenter_id = f"user_{random.randint(0, num_users - 1)}"
            commenter = users_db[commenter_id]
            comments_db[vid].append({
                'comment_id': str(uuid.uuid4())[:8],
                'user_id': commenter_id,
                'username': commenter['username'],
                'avatar': commenter['avatar'],
                'text': random.choice(COMMENT_TEMPLATES),
                'likes': random.randint(0, 2000),
                'timestamp': time.time() - random.randint(60, 86400 * 14),
            })

    for uid in list(users_db.keys()):
        num_likes = random.randint(10, min(50, len(videos_db)))
        vids = random.sample(list(videos_db.keys()), min(num_likes, len(videos_db)))
        for vid in vids:
            videos_db[vid]['liked_by'].add(uid)
            users_db[uid]['liked_videos'].append(vid)
            users_db[uid].setdefault('category_interests', {})
            cat = videos_db[vid].get('category', 'Unknown')
            users_db[uid]['category_interests'][cat] = users_db[uid]['category_interests'].get(cat, 0) + 1

    total_comments = sum(len(c) for c in comments_db.values())
    print(f"Seeded {len(users_db)} users, {len(videos_db)} videos, {total_comments} comments")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_current_user():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        uid = auth_tokens.get(token)
        if uid and uid in users_db:
            return users_db[uid]
    uid = request.args.get('user_id') or request.headers.get('X-User-Id')
    if uid and uid in users_db:
        return users_db[uid]
    return None


def format_count(n):
    if n >= 1000000:
        return f"{n / 1000000:.1f}M"
    if n >= 1000:
        return f"{n / 1000:.1f}K"
    return str(n)


# ---------------------------------------------------------------------------
# API: Auth
# ---------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    for u in users_db.values():
        if u['username'] == username:
            return jsonify({'error': 'Username taken'}), 409
    uid = f"user_{len(users_db)}"
    token = str(uuid.uuid4())
    users_db[uid] = {
        'user_id': uid,
        'username': username,
        'display_name': data.get('display_name', username.replace('_', ' ').title()),
        'avatar': generate_avatar_url(username),
        'bio': '',
        'followers': [],
        'following': [],
        'follower_count': 0,
        'following_count': 0,
        'liked_videos': [],
        'watched_videos': [],
        'category_interests': {},
        'is_verified': False,
        'total_likes': 0,
        'created_at': time.time(),
    }
    auth_tokens[token] = uid
    return jsonify({'token': token, 'user': _user_response(users_db[uid])})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    for uid, u in users_db.items():
        if u['username'] == username:
            token = str(uuid.uuid4())
            auth_tokens[token] = uid
            return jsonify({'token': token, 'user': _user_response(u)})
    return jsonify({'error': 'User not found'}), 404


@app.route("/api/auth/me", methods=["GET"])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(_user_response(user))


def _user_response(u):
    return {
        'user_id': u['user_id'],
        'username': u['username'],
        'display_name': u['display_name'],
        'avatar': u['avatar'],
        'bio': u['bio'],
        'follower_count': u['follower_count'],
        'following_count': u['following_count'],
        'is_verified': u.get('is_verified', False),
        'total_likes': u.get('total_likes', 0),
    }


# ---------------------------------------------------------------------------
# API: Feed
# ---------------------------------------------------------------------------

@app.route("/api/feed/foryou", methods=["GET"])
def feed_foryou():
    user = get_current_user()
    uid = user['user_id'] if user else None
    n = int(request.args.get('count', 5))
    if uid:
        videos = recommender.get_recommendations(uid, n=n, feed_type='foryou')
        # Blend in generated content based on configured ratio
        if gen_config.enabled:
            gen_pipeline.tick(users_db, videos_db)
            num_gen = max(1, int(n * gen_config.generated_content_ratio))
            gen_videos = gen_pipeline.get_generated_for_user(uid, users_db, videos_db, n=num_gen)
            for gv in gen_videos:
                gv['is_generated'] = True
                gv['is_liked'] = False
                gv['is_following'] = False
                if 'stats' not in gv:
                    gv['stats'] = {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
                if 'creator' not in gv:
                    gv['creator'] = {'user_id': 'ai', 'username': 'ai.generator', 'display_name': 'AI Generator', 'avatar': '', 'is_verified': True}
                if 'music' not in gv:
                    gv['music'] = {'name': 'AI Generated', 'artist': 'Neural Network'}
            # Insert generated videos at spaced positions in the feed
            for i, gv in enumerate(gen_videos):
                pos = min((i + 1) * 3, len(videos))
                videos.insert(pos, gv)
    else:
        videos = recommender._cold_start_recommendations(n)
    if user:
        for v in videos:
            if v:
                v.setdefault('is_liked', user['user_id'] in videos_db.get(v.get('video_id', ''), {}).get('liked_by', set()))
                v.setdefault('is_following', v.get('creator', {}).get('user_id', '') in user.get('following', []))
                v.setdefault('is_generated', False)
    return jsonify(videos)


@app.route("/api/feed/following", methods=["GET"])
def feed_following():
    user = get_current_user()
    if not user:
        return jsonify([])
    n = int(request.args.get('count', 5))
    videos = recommender.get_recommendations(user['user_id'], n=n, feed_type='following')
    for v in videos:
        if v:
            v['is_liked'] = user['user_id'] in videos_db.get(v['video_id'], {}).get('liked_by', set())
            v['is_following'] = True
    return jsonify(videos)


# Also keep legacy endpoints
@app.route("/random_videos", methods=['GET'])
def get_random_videos():
    vids = random.sample(list(videos_db.keys()), min(3, len(videos_db)))
    return jsonify([recommender._build_video_response(vid) for vid in vids])


@app.route("/next_video", methods=['GET'])
def next_video():
    user_id = request.args.get('user_id', 'guest')
    if user_id not in users_db:
        vids = recommender._cold_start_recommendations(1)
    else:
        vids = recommender.get_recommendations(user_id, n=1, feed_type='foryou')
    if vids:
        return jsonify(vids[0])
    return jsonify({'message': 'No videos available'}), 200


# ---------------------------------------------------------------------------
# API: Video interactions
# ---------------------------------------------------------------------------

@app.route("/api/video/<video_id>/like", methods=["POST"])
def toggle_like(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Auth required'}), 401
    v = videos_db.get(video_id)
    if not v:
        return jsonify({'error': 'Video not found'}), 404
    uid = user['user_id']
    liked_by = v.setdefault('liked_by', set())
    if uid in liked_by:
        liked_by.discard(uid)
        v['stats']['likes'] = max(v['stats']['likes'] - 1, 0)
        if video_id in user.get('liked_videos', []):
            user['liked_videos'].remove(video_id)
        is_liked = False
    else:
        liked_by.add(uid)
        v['stats']['likes'] += 1
        user.setdefault('liked_videos', []).append(video_id)
        recommender.update_user_embedding(uid, video_id, 'like')
        is_liked = True
    _update_engagement(video_id)
    return jsonify({
        'is_liked': is_liked,
        'likes': v['stats']['likes'],
        'likes_formatted': format_count(v['stats']['likes']),
    })


@app.route("/api/video/<video_id>/comment", methods=["POST"])
def add_comment(video_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Auth required'}), 401
    v = videos_db.get(video_id)
    if not v:
        return jsonify({'error': 'Video not found'}), 404
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Comment text required'}), 400
    comment = {
        'comment_id': str(uuid.uuid4())[:8],
        'user_id': user['user_id'],
        'username': user['username'],
        'avatar': user['avatar'],
        'text': text,
        'likes': 0,
        'timestamp': time.time(),
    }
    comments_db[video_id].append(comment)
    v['stats']['comment_count'] = len(comments_db[video_id])
    recommender.update_user_embedding(user['user_id'], video_id, 'comment')
    _update_engagement(video_id)
    return jsonify(comment)


@app.route("/api/video/<video_id>/comments", methods=["GET"])
def get_comments(video_id):
    page = int(request.args.get('page', 0))
    limit = int(request.args.get('limit', 30))
    all_comments = sorted(comments_db.get(video_id, []), key=lambda c: c['timestamp'], reverse=True)
    start = page * limit
    return jsonify({
        'comments': all_comments[start:start + limit],
        'total': len(all_comments),
        'has_more': start + limit < len(all_comments),
    })


@app.route("/api/video/<video_id>/share", methods=["POST"])
def share_video(video_id):
    v = videos_db.get(video_id)
    if not v:
        return jsonify({'error': 'Video not found'}), 404
    v['stats']['shares'] += 1
    user = get_current_user()
    if user:
        recommender.update_user_embedding(user['user_id'], video_id, 'share')
    _update_engagement(video_id)
    return jsonify({'shares': v['stats']['shares']})


@app.route("/api/video/<video_id>/view", methods=["POST"])
def record_view(video_id):
    v = videos_db.get(video_id)
    if not v:
        return jsonify({'error': 'Video not found'}), 404
    v['stats']['views'] += 1
    data = request.get_json() or {}
    watch_time = data.get('watch_time', 0)
    duration = v.get('duration', 10)
    if watch_time > 0:
        v['stats']['total_watch_time'] = v['stats'].get('total_watch_time', 0) + watch_time
        v['stats']['watch_count'] = v['stats'].get('watch_count', 0) + 1
        if v['stats']['watch_count'] > 0:
            completion = min(watch_time / max(duration, 1), 1.0)
            old_avg = v['stats'].get('avg_completion_rate', 0.5)
            count = v['stats']['watch_count']
            v['stats']['avg_completion_rate'] = old_avg + (completion - old_avg) / count
    user = get_current_user()
    if user:
        uid = user['user_id']
        user.setdefault('watched_videos', [])
        if video_id not in user['watched_videos']:
            user['watched_videos'].append(video_id)
        if watch_time > 0:
            recommender.update_user_embedding(uid, video_id, 'watch_time', min(watch_time / max(duration, 1), 2.0))
    _update_engagement(video_id)
    return jsonify({'views': v['stats']['views']})


@app.route("/update_interaction", methods=["POST"])
def update_interaction():
    data = request.get_json()
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    interaction_type = data.get('interaction_type')
    value = data.get('value', 1)
    if not all([user_id, video_id, interaction_type]):
        return jsonify({'error': 'Missing required parameters'}), 400
    if video_id in videos_db:
        recommender.update_user_embedding(user_id, video_id, interaction_type, value)
    return jsonify({'message': 'Interaction updated successfully'})


def _update_engagement(video_id):
    v = videos_db.get(video_id)
    if not v:
        return
    s = v['stats']
    views = max(s['views'], 1)
    s['engagement_score'] = (s['likes'] * 2 + s['comment_count'] * 3 + s['shares'] * 5) / views


# ---------------------------------------------------------------------------
# API: User / Social
# ---------------------------------------------------------------------------

@app.route("/api/user/<user_id>", methods=["GET"])
def get_user(user_id):
    u = users_db.get(user_id)
    if not u:
        return jsonify({'error': 'User not found'}), 404
    resp = _user_response(u)
    current = get_current_user()
    if current:
        resp['is_following'] = user_id in current.get('following', [])
    return jsonify(resp)


@app.route("/api/user/<user_id>/follow", methods=["POST"])
def toggle_follow(user_id):
    current = get_current_user()
    if not current:
        return jsonify({'error': 'Auth required'}), 401
    target = users_db.get(user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404
    if user_id == current['user_id']:
        return jsonify({'error': 'Cannot follow yourself'}), 400
    if user_id in current.get('following', []):
        current['following'].remove(user_id)
        current['following_count'] = len(current['following'])
        if current['user_id'] in target.get('followers', []):
            target['followers'].remove(current['user_id'])
        target['follower_count'] = len(target.get('followers', []))
        is_following = False
    else:
        current.setdefault('following', []).append(user_id)
        current['following_count'] = len(current['following'])
        target.setdefault('followers', []).append(current['user_id'])
        target['follower_count'] = len(target.get('followers', []))
        is_following = True
    return jsonify({
        'is_following': is_following,
        'follower_count': target['follower_count'],
    })


# ---------------------------------------------------------------------------
# API: Search / Discover
# ---------------------------------------------------------------------------

@app.route("/api/discover", methods=["GET"])
def discover():
    q = request.args.get('q', '').strip().lower()
    if q:
        results = []
        for vid, v in videos_db.items():
            searchable = f"{v.get('description', '')} {v.get('category', '')} {' '.join(v.get('tags', []))}".lower()
            if q in searchable:
                results.append(recommender._build_video_response(vid))
        return jsonify(results[:20])
    trending = sorted(videos_db.keys(), key=lambda vid: videos_db[vid]['stats']['engagement_score'], reverse=True)
    return jsonify([recommender._build_video_response(vid) for vid in trending[:20]])


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

@app.route("/videos/<filename>", methods=['GET'])
def serve_video(filename):
    try:
        return send_from_directory(VIDEOS_DIR, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Video not found'}), 404


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# API: Generation Pipeline
# ---------------------------------------------------------------------------

@app.route("/api/generation/status", methods=["GET"])
def generation_status():
    return jsonify(gen_pipeline.get_pipeline_status())


@app.route("/api/generation/profile/<user_id>", methods=["GET"])
def generation_profile(user_id):
    """Get interest profile and what prompt would be generated for this user."""
    return jsonify(gen_pipeline.compose_prompt_preview(user_id, users_db, videos_db))


@app.route("/api/generation/trigger", methods=["POST"])
def generation_trigger():
    """Manually trigger a generation tick (for testing/development)."""
    gen_pipeline.tick(users_db, videos_db)
    return jsonify(gen_pipeline.get_pipeline_status())


@app.route("/api/generation/preview", methods=["GET"])
def generation_preview():
    """Preview generated videos available for the current user."""
    user = get_current_user()
    if not user:
        return jsonify([])
    videos = gen_pipeline.get_generated_for_user(user['user_id'], users_db, videos_db, n=5)
    return jsonify(videos)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("Starting Monolith Recommendation Server...")
    seed_data()
    gen_pipeline.initialize(users_db, videos_db)
    print(f"Generation pipeline: {gen_pipeline.get_pipeline_status()['num_clusters']} user clusters")
    print("Server ready.")
    app.run(debug=True, host='0.0.0.0', port=5050)
