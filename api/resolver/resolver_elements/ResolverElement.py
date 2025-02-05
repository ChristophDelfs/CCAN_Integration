class ResolverElement:
    def get_resolver_key(self):
        raise NotImplementedError

    def get_lark_description(self):
        raise NotImplementedError

    def get_transformer_method(self):
        raise NotImplemented
    
    def get_resolver_method(self):
        raise NotImplemented

    __
    