# email-mcp -- MCP Server Capabilities

**Instructions for LLM:** This file must contain 3,000+ words describing the server's complete capabilities.
Include: all tools with parameters, all prompts, all resources, configuration options, environment variables,
data sources, and integration points. Every tool must have its purpose, parameters, and return format documented.

## Server Overview

[Write 2-3 paragraphs describing what this MCP server does, its domain, and key features.]

## Tools

- **get_logs**: get_logs - **clear_logs**: clear_logs - **export_logs**: export_logs - **suggest_email_subject**: suggest_email_subject - **email_agentic_assist**: email_agentic_assist - **show_email_status_card**: show_email_status_card - **show_inbox_card**: show_inbox_card - **show_services_card**: show_services_card - **health**: health - **main_stdio**: main(stdio) - **main_http**: main(http) - **main_sse**: main(sse) - **get_status**: get_status - **get_capabilities**: get_capabilities - **list_tools**: list_tools - **list_services**: list_services - **get_service**: get_service - **add_service**: add_service - **update_service**: update_service - **delete_service**: delete_service - **test_service**: test_service - **quick_setup**: quick_setup - **check_proton_bridge**: check_proton_bridge - **get_stats**: get_stats - **get_inbox**: get_inbox - **get_email_detail**: get_email_detail - **mark_email_as_read**: mark_email_as_read - **mark_email_as_unread**: mark_email_as_unread - **delete_email**: delete_email - **search_emails**: search_emails - **list_folders**: list_folders - **create_folder**: create_folder - **delete_folder**: delete_folder - **rename_folder**: rename_folder - **get_attachment**: get_attachment - **get_unified_inbox**: get_unified_inbox - **send_email**: send_email - **send_bulk**: send_bulk - **list_drafts**: list_drafts - **save_draft**: save_draft - **update_draft**: update_draft - **delete_draft**: delete_draft - **list_contacts**: list_contacts - **add_contact**: add_contact - **update_contact**: update_contact - **delete_contact**: delete_contact - **import_contacts**: import_contacts - **import_google_contacts**: import_google_contacts - **import_microsoft_contacts**: import_microsoft_contacts - **list_groups**: list_groups - **curated_list_lists**: curated_list_lists - **curated_list_detail**: curated_list_detail - **curated_list_import**: curated_list_import - **template_list**: template_list - **template_add**: template_add - **template_delete**: template_delete - **signature_get**: signature_get - **signature_set**: signature_set - **signature_delete**: signature_delete - **schedule_create**: schedule_create - **schedule_list**: schedule_list - **schedule_cancel**: schedule_cancel - **list_skills**: list_skills - **get_skill_content**: get_skill_content - **get_llm_models**: get_llm_models - **configure_llm**: configure_llm - **chat**: chat - **parse_config**: parse_config - **improve_text**: improve_text - **expand_text**: expand_text - **get_service_types**: get_service_types - **lab_start**: lab_start - **lab_stop**: lab_stop - **lab_status**: lab_status - **lab_list_emails**: lab_list_emails - **lab_get_email**: lab_get_email - **lab_clear_emails**: lab_clear_emails - **lab_inject_email**: lab_inject_email - **lab_generate_emails**: lab_generate_emails - **lab_forward_email**: lab_forward_email - **run_workflow**: run_workflow - **watcher_start**: watcher_start - **watcher_stop**: watcher_stop - **watcher_status**: watcher_status - **check_spam**: check_spam - **auto_list_rules**: auto_list_rules - **auto_add_rule**: auto_add_rule - **auto_update_rule**: auto_update_rule - **auto_delete_rule**: auto_delete_rule - **auto_list_pending**: auto_list_pending - **auto_approve_pending**: auto_approve_pending - **auto_reject_pending**: auto_reject_pending - **auto_respond_now**: auto_respond_now

## Configuration

[Document all environment variables, their defaults, and purposes.]

## Data Sources

[Document any databases, APIs, or files the server reads.]
