# x-aoutagent
# AGENTS.md — X自動運用システム

## プロジェクト概要

複数のXアカウントをAIエージェントで完全自動運用するシステム。
PM Agentが全アカウントを統括し、各Account Agentがアカウント個別の運用を担う。
最終目的は全アカウントのフォロワー数を伸ばすこと。

---

## ディレクトリ構成

```
/
├── AGENTS.md
├── .env                        # APIキー（gitignore必須）
├── main.py                     # スケジューラー起動エントリポイント
├── requirements.txt
├── accounts/                   # アカウントごとの初期設計ファイル
│   └── {account_id}/
│       ├── profile.md          # アカウント設計・方針
│       ├── competitors.md      # 競合分析レポート
│       ├── rules.md            # 禁止事項・ルール
│       └── kpi.md              # KPI設定
├── media/                      # 投稿用メディア（gitignore）
│   └── {account_id}/
│       ├── images/
│       └── videos/
├── logs/                       # AIエージェント間の議事録・ログ
│   ├── daily/
│   │   └── {YYYY-MM-DD}/
│   │       └── {account_id}.md
│   └── weekly/
│       └── {YYYY-MM-DD}/
│           └── mtg.md
├── agents/
│   ├── pm_agent.py             # PM Agentのコア処理
│   ├── account_agent.py        # Account Agentのコア処理
│   └── ai_client.py            # AIプロバイダー共通クライアント
├── services/
│   ├── twitter_cli.py          # twitter-cliラッパー
│   ├── x_api.py                # X API（投稿・メディア）
│   ├── scheduler.py            # schedule + threading
│   └── shadowban.py            # シャドウバンチェック
├── db/
│   ├── supabase_client.py      # Supabaseクライアント
│   └── models.py               # テーブル定義
└── dashboard/                  # WebダッシュボードUI
    ├── app.py                  # FastAPI or Flask
    ├── templates/
    └── static/
```

---

## 技術スタック

- **言語**: Python 3.11+
- **DB**: Supabase（PostgreSQL）
- **スケジューラ**: schedule + threading（Mac常駐）
- **X操作（取得・検索）**: twitter-cli（Cookie認証）
- **X操作（投稿・メディア）**: X API（従量課金）
- **ダッシュボード**: FastAPI + Jinja2（localhost）
- **メディア保存**: ローカル `/media/{account_id}/`
- **ログ保存**: ローカル `/logs/`

---

## 環境変数（.env）

```
# AI APIs
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# X API
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN_{ACCOUNT_ID}=      # アカウントごと
X_ACCESS_TOKEN_SECRET_{ACCOUNT_ID}=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
```

---

## Supabaseテーブル設計

### accounts
```sql
id              uuid PRIMARY KEY
account_id      text UNIQUE         -- Xのユーザー名
display_name    text
phase           text                -- shadowban_recovery / launch / growth / mature
is_shadowbanned boolean DEFAULT false
ai_provider     text                -- anthropic / openai / google
ai_model        text                -- モデル名
forbidden_content text[]            -- 禁止コンテンツリスト
forbidden_actions text[]            -- 禁止アクションリスト
post_frequency  int                 -- 1日の投稿数
created_at      timestamptz DEFAULT now()
updated_at      timestamptz DEFAULT now()
```

### posts
```sql
id              uuid PRIMARY KEY
account_id      text REFERENCES accounts(account_id)
content         text
purpose         text                -- 投稿目的（自由記述）
media_paths     text[]              -- ローカルメディアパス
scheduled_at    timestamptz
posted_at       timestamptz
is_posted       boolean DEFAULT false
is_failed       boolean DEFAULT false
likes           int DEFAULT 0
retweets        int DEFAULT 0
replies         int DEFAULT 0
bookmarks       int DEFAULT 0
impressions     int DEFAULT 0
tweet_id        text                -- XのツイートID
created_at      timestamptz DEFAULT now()
```

### knowledge
```sql
id              uuid PRIMARY KEY
scope           text                -- global / account-specific
account_id      text                -- account-specificの場合のみ
content         text                -- ナレッジ本文
confidence      text                -- hypothesis / mid / high
category        text                -- 施策カテゴリ
validation_count int DEFAULT 0      -- 閾値超え回数
last_validated_at timestamptz
created_at      timestamptz DEFAULT now()
updated_at      timestamptz DEFAULT now()
```

### tactics
```sql
id              uuid PRIMARY KEY
account_id      text REFERENCES accounts(account_id)
description     text                -- 施策内容
knowledge_id    uuid REFERENCES knowledge(id)
success_count   int DEFAULT 0
fail_count      int DEFAULT 0
score_threshold int DEFAULT 50      -- 確度UP判定の閾値
created_at      timestamptz DEFAULT now()
```

### daily_reports
```sql
id              uuid PRIMARY KEY
account_id      text REFERENCES accounts(account_id)
report_date     date
reflection      text                -- 反省文
hypothesis      text                -- 次の仮説
pm_instruction  text                -- PMからの施策指示
created_at      timestamptz DEFAULT now()
```

### weekly_reports
```sql
id              uuid PRIMARY KEY
week_start      date
follower_summary jsonb              -- アカウント別フォロワー前週比
impression_summary jsonb
tactics_summary text
evaluation      text                -- 効いた・効かなかった
next_week_plan  text
created_at      timestamptz DEFAULT now()
```

### schedules
```sql
id              uuid PRIMARY KEY
account_id      text REFERENCES accounts(account_id)
post_id         uuid REFERENCES posts(id)
scheduled_at    timestamptz
is_checked      boolean DEFAULT false  -- 人間がチェックしたか
created_at      timestamptz DEFAULT now()
```

### notifications
```sql
id              uuid PRIMARY KEY
type            text                -- post_failed / pm_question / shadowban_resolved
account_id      text
message         text
is_read         boolean DEFAULT false
created_at      timestamptz DEFAULT now()
```

### ai_action_models
```sql
id              uuid PRIMARY KEY
action_name     text UNIQUE         -- アクション名（下記一覧参照）
ai_provider     text
ai_model        text
updated_at      timestamptz DEFAULT now()
```

---

## AIアクション一覧とデフォルトモデル

以下のアクションそれぞれにAIモデルをWeb UIから設定可能。

| アクション | 説明 | デフォルト推奨 |
|---|---|---|
| pm_weekly_mtg | 週次MTG進行・方針決定 | claude-opus-4-6 |
| pm_weekly_report | 週次レポート生成 | claude-opus-4-6 |
| pm_knowledge_promotion | ナレッジ昇格判断 | claude-opus-4-6 |
| pm_daily_review | 毎朝の反省レビュー・施策指示 | claude-opus-4-6 |
| pm_question | 判断しきれない時の質問生成 | claude-opus-4-6 |
| account_setup_dialogue | 新規アカウント設計対話 | claude-opus-4-6 |
| account_competitor_research | 競合リサーチ・初期設計生成 | claude-sonnet-4-6 |
| account_daily_reflection | 日次反省レポート生成 | claude-sonnet-4-6 |
| account_daily_tactic | 日次施策立案 | claude-sonnet-4-6 |
| account_post_generation | 投稿文生成 | claude-sonnet-4-6 |
| account_reply_generation | リプライ返信文生成 | claude-sonnet-4-6 |
| account_media_selection | メディア選定 | claude-haiku-4-5-20251001 |
| account_shadowban_action | シャドバン期アクション選定 | claude-haiku-4-5-20251001 |
| search_result_summary | 検索結果整理・要約 | claude-haiku-4-5-20251001 |

---

## アカウントフェーズと挙動

### shadowban_recovery（シャドウバン解除期）
- 毎日の固定アクション（Account Agentが初期設計を元に自動選定）
  - 同ジャンルアカウントにいいね × 20
  - ツイート × 2
  - 引用RT × 1
  - リプ × 1
- 反省・施策・ナレッジ更新はスキップ
- 毎朝シャドウバンチェック（twitter search）
- 解除確認 → ダッシュボードに通知
- 週の中盤に解除された場合はその週は基本アクション継続、次の月曜から立ち上げ期へ

### launch / growth / mature
- 通常の日次処理を実行

---

## 日次スケジュール（毎日 6:00am）

```
1. 全アカウントのシャドウバンチェック（twitter search）
2. 2日前の投稿エンゲージメントを取得（twitter-cli user-posts）
3. Account Agent: 数値+投稿内容を記録 → 反省レポート+次の仮説を生成
4. PM Agent: 全アカウントの反省レポートを読んで施策指示・ナレッジ更新
5. Account Agent: 今日の施策を自分で考えて投稿内容・目的を生成
6. Account Agent: メディアフォルダから画像・動画を選定
7. スケジューラーに投稿予約をセット
8. Dashboard更新（投稿スケジュール・チェックボックス・通知）
```

## 週次スケジュール（毎週月曜 6:00am、日次処理の後に実行）

```
1. 全アカウントの週次データを集計
2. 各Account Agentが週次報告を生成
3. PM Agentが全報告を読んで会議形式でMTGを実施
4. PM Agentがナレッジのスコープ・確度を整理（global昇格判断）
5. PM Agentが各Account Agentに今週の方針・KPIを渡す
6. 週次レポートを生成してダッシュボードに表示
7. /logs/weekly/{date}/mtg.md に全発言ログを保存
```

## リプライ監視（毎時）

```
1. twitter-cliでリプライ・メンションを取得（AIなし）
2. 新着リプライがあればAccount Agentが返信文を生成
3. X APIで即時返信
```

---

## ナレッジ設計

- スコープ: `global` / `account-specific`
- 確度: `hypothesis` → `mid` → `high`
  - 同施策カテゴリでスコアが閾値を3回以上超えたら昇格
- 賞味期限: 一定期間（デフォルト90日）再検証なしで確度自動ダウン
- メインナレッジ（global）にはXのアルゴリズム情報・禁止事項を人間が手動記入

### エージェントの参照優先順位（最重要）
1. メインナレッジ（global / アルゴリズム・禁止事項） ← 絶対遵守
2. アカウントナレッジ（high確度）
3. アカウントナレッジ（mid確度）
4. 週次方針

---

## X検索の使い方

- twitter-cli searchを使用（APIコスト追加なし）
- PM・各Account Agentが自律的に必要と判断したら実行
- 用途: トレンド把握・競合分析・バズ投稿へのリアクション投稿

---

## シャドウバンチェック

- `twitter search "{account_id} filter:retweets"` で自分のツイートが検索結果に出るか確認
- 結果をaccountsテーブルの `is_shadowbanned` に保存
- 検索バンのみ検出（リプライバン・サジェストバンは対象外）

---

## 投稿失敗時の処理

1. notificationsテーブルにtype=post_failedで記録
2. ダッシュボードに即時通知表示
3. リトライは3回まで（1分間隔）

---

## BANリスク対策

- 操作間にランダムディレイを挿入（1〜3秒）
- 1日の操作回数に上限を設ける（アカウントごとに設定）
- IP変更なし（同一IPで複数アカウントは正常運用の範囲）

---

## ダッシュボード画面構成

1. **ホーム** - 通知・要確認事項・今日のスケジュール概要
2. **アナリティクス（個別）** - フォロワー推移・インプレ・エンゲージメント率・投稿別パフォーマンス（日次/週次/月次切替）
3. **アナリティクス（比較）** - 全アカウント横並び比較
4. **投稿スケジュール** - 日時・内容・メディアサムネイル・チェックボックス
5. **週次レポート** - レポート一覧・閲覧
6. **AIログ・議事録** - 日付カレンダーで選択・エージェント別色分け・キーワード検索
7. **アカウント管理** - 新規作成・設定編集・フェーズ確認
8. **設定**
   - APIキー管理（Anthropic / OpenAI / Google / X API）
   - AIモデル設定（アクションごと）
   - アカウント設定（禁止事項・禁止アクション・投稿頻度）

---

## 新規アカウント作成フロー

1. ダッシュボードのWeb UI上でAIと対話形式で質問に答える
   - ターゲット層・ジャンル・トーン・禁止事項・禁止アクション等
2. 競合アカウントを最大5つ入力
3. Account AgentがTwitter searchで競合をリサーチ
4. 初期設計ファイルを自動生成・保存
   - `/accounts/{account_id}/profile.md`
   - `/accounts/{account_id}/competitors.md`
   - `/accounts/{account_id}/rules.md`
   - `/accounts/{account_id}/kpi.md`
5. Supabaseのaccountsテーブルにレコード作成
6. フェーズを `shadowban_recovery` でスタート

---

## コーディング規約

- Python 3.11+
- 型ヒントを必ず付ける
- 非同期処理は asyncio を使用
- エラーハンドリングは全ての外部API呼び出しに必須
- ログは `/logs/daily/{date}/{account_id}.md` に追記形式で保存
- 環境変数は `.env` から読み込み、コードにハードコードしない
- テストは `tests/` ディレクトリに配置
