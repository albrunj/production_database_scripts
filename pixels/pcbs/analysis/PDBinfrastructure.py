import itkdb
import itkdb.exceptions as itkX


#####################
### Useful functions
#####################

def AuthenticateUser(ac1,ac2):
    try:
        user = itkdb.core.User(accessCode1=ac1, accessCode2=ac2)
        user.authenticate()
        client = itkdb.Client(user=user)
        return client
    except itkX.BadRequest as b: # catch double registrations
        print("authenticate: went wrong")
        print(str(b)[str(b).find('"message": ')+len('"message": '):str(b).find('"paramMap"')-8]) # sucks
    return None


def DbAccess(client, myAction, inData, listFlag=False):
    outData=None
    if listFlag:
        outData = list(client.get(myAction, json=inData ) )
    else:
        outData = client.get(myAction, json=inData)
    return outData


def GetInstList(client):
    myList = list(client.get('listInstitutions'))
    return myList


def GetProjList(client):
    myList= list(client.get('listProjects'))
    return myList


# debugging
# myClient=AuthenticateUser("stripsKenny","pixelsKenny")
# user=myClient.get('getUser', json={'userIdentity': myClient.user.identity})
# user['firstName']
