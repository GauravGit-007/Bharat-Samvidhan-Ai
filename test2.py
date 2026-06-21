import traceback
try:
    print('Testing CrossEncoder import...')
    from sentence_transformers import CrossEncoder
    print('Success CrossEncoder import!')
    
    print('Testing model load...')
    from src.config.settings import settings
    model = CrossEncoder(settings.RERANK_MODEL, device='cpu')
    print('Success model load!')
    
except Exception as e:
    traceback.print_exc()
