import graphene
from graphene_django import DjangoObjectType

from factsheet.models import FactsheetModel
from factsheet.models import FundingSourceModel

class FundingSourceType(DjangoObjectType):
    class Meta:
        model = FundingSourceModel

class FundingSourceInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)
    uri =  graphene.String(required=True)

class FactsheetType(DjangoObjectType):
    class Meta:
        model = FactsheetModel

class FactsheetInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    uri =  graphene.String(required=True)
    funding_sources = graphene.List(graphene.Int)

class Query(graphene.ObjectType):
    factsheets = graphene.List(FactsheetType)
    factsheet_by_id = graphene.Field(FactsheetType, id=graphene.Int())
    funding_sources = graphene.List(FundingSourceType)

    def resolve_factsheets(self, info):
        return FactsheetModel.objects.all()

    def resolve_factsheet_by_id(self, info, id):
        return FactsheetModel.objects.get(id=id)

    def resolve_funding_sources(self, info):
        return FundingSourceModel.objects.all()

class CreateFundingSource(graphene.Mutation):
    name = graphene.String()
    uri = graphene.String()

    class Arguments:
        name = graphene.String()
        uri = graphene.String()

    def mutate(self, info, name, uri):
        funding_source = FundingSourceModel(name=name, uri=uri)
        funding_source.save()

        return CreateFundingSource(
            name=funding_source.name,
            uri=funding_source.uri,
        )

class CreateFactsheet(graphene.Mutation):
    name = graphene.String()
    uri = graphene.String()
    funding_sources = graphene.List(FundingSourceType)

    class Arguments:
        name = graphene.String()
        uri = graphene.String()
        funding_sources = graphene.List(FundingSourceInput)

    def mutate(self, info, name, uri, funding_sources):
        funding_source_list = [FactsheetModel.objects.filter(funding_source=funding_source.id).update_or_create(**funding_source) for funding_source in funding_sources]
        return CreateFactsheet(name=name, uri=uri, funding_sources=funding_source_list)


class Mutation(graphene.ObjectType):
    create_factsheet = CreateFactsheet.Field()
    create_funding_source = CreateFundingSource.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)
