import graphene
from graphene_django import DjangoObjectType

from factsheet.models import UserModel

class UserType(DjangoObjectType):
    class Meta:
        model = UserModel


class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.Int())

    def resolve_users(self, info):
        return UserModel.objects.all()

    def resolve_user_by_id(self, info, id):
        return UserModel.objects.get(id=id)


class CreateUser(graphene.Mutation):
    id = graphene.Int()
    firstName = graphene.String()
    lastName = graphene.String()

    class Arguments:
        firstName = graphene.String()
        lastName = graphene.String()

    def mutate(self, info, firstName, lastName):
        user = UserModel(firstName=firstName, lastName=lastName)
        user.save()

        return CreateUser(
            id=user.id,
            firstName=user.firstName,
            lastName=user.lastName,
        )


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()


schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)
