insert into public.ai_action_models (action_name, ai_provider, ai_model)
values
    ('pm_weekly_mtg', 'anthropic', 'claude-opus-4-6'),
    ('pm_weekly_report', 'anthropic', 'claude-opus-4-6'),
    ('pm_knowledge_promotion', 'anthropic', 'claude-opus-4-6'),
    ('pm_daily_review', 'anthropic', 'claude-opus-4-6'),
    ('pm_question', 'anthropic', 'claude-opus-4-6'),
    ('account_setup_dialogue', 'anthropic', 'claude-opus-4-6'),
    ('account_competitor_research', 'anthropic', 'claude-sonnet-4-6'),
    ('account_daily_reflection', 'anthropic', 'claude-sonnet-4-6'),
    ('account_daily_tactic', 'anthropic', 'claude-sonnet-4-6'),
    ('account_post_generation', 'anthropic', 'claude-sonnet-4-6'),
    ('account_reply_generation', 'anthropic', 'claude-sonnet-4-6'),
    ('account_media_selection', 'anthropic', 'claude-haiku-4-5-20251001'),
    ('account_shadowban_action', 'anthropic', 'claude-haiku-4-5-20251001'),
    ('search_result_summary', 'anthropic', 'claude-haiku-4-5-20251001')
on conflict (action_name)
do update set
    ai_provider = excluded.ai_provider,
    ai_model = excluded.ai_model,
    updated_at = now();
