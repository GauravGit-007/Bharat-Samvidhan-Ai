import traceback
try:
    from src.retrieval.retriever import Retriever
    r = Retriever()
    print('Success Retriever init!')
    
    from src.retrieval.generator import Generator
    g = Generator()
    print('Success Generator init!')
    
    import tests.stress_test_concurrency as st
    print('Success stress_test_concurrency import!')
    
except Exception as e:
    traceback.print_exc()
