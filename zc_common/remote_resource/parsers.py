"""
Parsers
"""
from rest_framework_json_api import parsers
from rest_framework.exceptions import ParseError

from rest_framework_json_api import utils, exceptions


class JSONParser(parsers.JSONParser):

    @staticmethod
    def parse_metadata(result):
        metadata = result.get('meta')
        if metadata:
            return {'_meta': metadata}
        else:
            return {}

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = parsers.JSONParser.parse(self, stream, media_type=media_type, parser_context=parser_context)

        data = result.get('data')

        if data:
            from rest_framework_json_api.views import RelationshipView
            if isinstance(parser_context['view'], RelationshipView):
                # We skip parsing the object as JSONAPI Resource Identifier Object and not a regular Resource Object
                if isinstance(data, list):
                    for resource_identifier_object in data:
                        if not (resource_identifier_object.get('id') and resource_identifier_object.get('type')):
                            raise ParseError(
                                'Received data contains one or more malformed JSONAPI Resource Identifier Object(s)'
                            )
                elif not (data.get('id') and data.get('type')):
                    raise ParseError('Received data is not a valid JSONAPI Resource Identifier Object')

                return data

            request = parser_context.get('request')

            # Check for inconsistencies
            resource_name = utils.get_resource_name(parser_context)
            view = parser_context.get('view')
            if data.get('type') != resource_name and request.method in ('PUT', 'POST', 'PATCH'):
                raise exceptions.Conflict(
                    "The resource object's type ({data_type}) is not the type "
                    "that constitute the collection represented by the endpoint ({resource_type}).".format(
                        data_type=data.get('type'),
                        resource_type=resource_name
                    )
                )

            # Construct the return data
            parsed_data = {'id': data.get('id')}
            parsed_data.update(self.parse_attributes(data))
            parsed_data.update(self.parse_relationships(data))
            parsed_data.update(self.parse_metadata(result))
            return parsed_data

        else:
            raise ParseError('Received document does not contain primary data')
