import requests



class jcList:
    def __init__(self, api_spec):
        self.api_spec = api_spec

    def list_opids(self, path_specified:str=None) -> list:
        operation_ids = []

        for _, methods in self.api_spec['paths'].items():
            if path_specified and path_specified != _:
                continue
            
            for _, method_data in methods.items():
                if 'operationId' in method_data:
                    operation_id = method_data['operationId']
                    operation_ids.append(operation_id)

        return self.sort_list(operation_ids)
    
    def sort_list(self,items:list) -> list:
        return sorted(items, key=lambda i: len(i), reverse=True)

    def list_opids_dev(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        operation_ids = []
        for path, methods in paths.items():
            for method, details in methods.items():
                operation_id = details.get('operationId')
                if operation_id:
                    operation_ids.append(operation_id)
        
        return operation_ids

    def list_schemas(self, path=None):
        components = self.api_spec.get('components', {})
        schemas = components.get('schemas', {})
        
        if path:
            paths = self.api_spec.get('paths', {})
            path_details = paths.get(path, {})
            schemas = {k: v for k, v in schemas.items() if k in path_details}
        
        return schemas

    def list_paths(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        return paths

    def list_parameters(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        parameters = {}
        for path, methods in paths.items():
            parameters[path] = {}
            for method, details in methods.items():
                params = details.get('parameters', [])
                parameters[path][method] = params
        
        return parameters

    def list_response_codes(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        response_codes = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                responses = details.get('responses', {})
                response_codes[path] = list(responses.keys())
        
        return response_codes

    def list_examples(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        examples = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                request_body = details.get('requestBody', {})
                content = request_body.get('content', {})
                for media_type, media_details in content.items():
                    example = media_details.get('example')
                    if example:
                        examples[path] = example
        
        return examples

    def list_tags(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        tags = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                method_tags = details.get('tags', [])
                for tag in method_tags:
                    if tag not in tags:
                        tags[tag] = []
                    tags[tag].append(path)
        
        return tags

    def list_descriptions(self, path=None):
        paths = self.api_spec.get('paths', {})
        
        if path:
            paths = {path: paths.get(path, {})}
        
        descriptions = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                description = details.get('description', 'No description provided')
                descriptions[path] = description
        
        return descriptions

    def list_response_headers(self, path=None):
        paths = self.api_spec.get('paths', {})
        if path:
            paths = {path: paths.get(path, {})}
        
        response_headers = {}
        for path, methods in paths.items():
            for method, details in methods.items():
                responses = details.get('responses', {})
                for status_code, response in responses.items():
                    headers = response.get('headers', {})
                    if headers:
                        response_headers[path] = headers
                    
        return response_headers

    def list_pydantic_models(self):
        """List all Pydantic models extracted from the API"""

        if not self.api_spec:
            print(" → No API specification loaded")
            return
            
        from ..engines.pydantic_engine import PydanticModelExtractor
        
        # Use the existing model extractor
        extractor = PydanticModelExtractor(self.api_spec)
        return extractor.extract_models()
        
