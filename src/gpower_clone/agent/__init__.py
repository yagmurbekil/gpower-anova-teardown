"""MCP sunucusuna istemci olarak bağlanan kural tabanlı doğal dil ajanı (CONTRACT §8).

Dil modeli kullanmaz; API anahtarı ve internet bağlantısı gerektirmez. Sorumluluklar:
    rules       — sözlük ve düzenli ifadeler (TR/EN eş anlamlılar, modlar, analiz türleri)
    parser      — metinden alan değerlerini, modu ve belirsizlikleri deterministik çıkarma
    core        — konuşma durumu; MCP ile doğrulama ve hesap; soru sorma kararı
    response    — deterministik yanıt metinleri
    mcp_client  — bağlantı (MCPConnection), araç keşfi (ToolCatalog), araç çağrısı (ToolInvoker)
    audit       — `logs/agent_calls.jsonl` denetim kaydı, gizli bilgi maskeleme
    evaluate    — senaryo değerlendirmesi
"""
