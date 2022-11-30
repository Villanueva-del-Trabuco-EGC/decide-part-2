from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census
from .forms import AtributosUser
from voting.models import Voting
from census import census_utils as Utils

class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')

def export_census(request, voting_id):
    template = loader.get_template('export_census.html')
    formulario = AtributosUser()
    voting = None
    census = []
    census_text = ''
    voters = []
    index_list = []

    if request.method == 'POST':
        formulario = AtributosUser(request.POST)
        if formulario.is_valid():
            voting = Voting.objects.filter(id=voting_id).values()[0]
            census = Census.objects.filter(voting_id=voting_id).values()
            index_list = [i for i in range(0,len(census))]
            data = Utils.get_csvtext_and_voters(formulario.cleaned_data['user_atributes'], census)
            census_text = data[0]
            voters = data[1]

    context = {
        'formulario':formulario,
        'voting':voting,
        'census':census,
        'census_text':census_text,
        'voters':voters,
        'index':index_list,
    }

    return HttpResponse(template.render(context, request))
