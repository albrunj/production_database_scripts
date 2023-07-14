#---------------------------------------------------
#
# The set of structures for holding the data
# For the objects in DB that we want to scan.
# --VF, 2021-09-06
#
#---------------------------------------------------
import logging
import numbers

from tabulate import tabulate

from strips.sensors.approvals.summary_data import ADD_KEYS
from strips.sensors.approvals.summary_data import DESIGN
from strips.sensors.approvals.summary_data import FINAL_STATES
from strips.sensors.approvals.summary_data import HEAD_CASE
from strips.sensors.approvals.summary_data import LIMITS
from strips.sensors.approvals.summary_data import MERGE_KEYS
from strips.sensors.approvals.summary_data import NEED_ALL_IDs
from strips.sensors.approvals.summary_data import NEED_ALL_IDs_KEK
from strips.sensors.approvals.summary_data import NEED_SAMPLE_IDs
from strips.sensors.approvals.summary_data import NEED_TODO_IDs
from strips.sensors.approvals.summary_data import TABLE_KEYS
from strips.sensors.SensorSNUtils import makeSN_sensor

# for our links to the DB web viewer
html_pref_test_ = "https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/dcb3f6d1f130482581ba1e7bbe34413c/testRunView?id="
html_pref_obj_  = "https://uuappg01-eu-w-1.plus4u.net/ucl-itkpd-maing01/dcb3f6d1f130482581ba1e7bbe34413c/componentView?code="
cPink   = ' bgcolor=\"#ff00ff\"'
cRed    = ' bgcolor=\"#ff0000\"'
cYellow = ' bgcolor=\"#ffff00\"'
cGreen  = ' bgcolor=\"#00ff00\"'

TESTS = NEED_ALL_IDs + NEED_SAMPLE_IDs + NEED_TODO_IDs

#____________________________
# QA flags for batch: setup at initialization time, or through updateQA call
# QA flags for sensors: setup at ini time, or through updateQA call
# => if the batch is composed of sensors with a different QA flags at ini,
# and the updateQA is not called, they won't be synchronized. Not a problem?
#
# Further handling if the batch is failed (all sensors to fail? Maybe! )
# or returned (all sensors to return? Probably not, leave as is with the flag)
#____________________________
class Batch():
    def __init__(self, batch_name,
                 ID,
                 isReal,
                 Type,
                 listWafers,
                 listMAINs,
                 listHalfmoons,
                 listQAminis,
                 listQAchips,
                 ifReturned=False,ifFailed=False,QATC=None,QACCE=None,
                 nReady=0,nUnhappy=0,nDamaged=0,nPhantom=0,nSpecial=0,nReturned=0,
                 nTestOK=0, nUncert=0, nTFully=0, nTested=None, testedAt=""):
        self._bName    = batch_name # general info
        self._ID       = ID
        self._isReal   = isReal
        self._Type     = Type
        self._lWafers  = listWafers # lists of components
        self._lMAINs   = listMAINs    
        self._lHMs     = listHalfmoons
        self._lQAminis = listQAminis  
        self._lQAchips = listQAchips
        self._ifReturned = ifReturned # these are only flags (no processing now)
        self._ifFailed   = ifFailed
        self._qaTC       = QATC
        self._qaCCE      = QACCE
        self._nReady    = nReady     # classified counts
        self._nUnhappy  = nUnhappy
        self._nDamaged  = nDamaged
        self._nPhantom  = nPhantom
        self._nSpecial  = nSpecial
        self._nReturned = nReturned
        self._nTestOK  = nTestOK    # tests counts
        self._nUncert  = nUncert
        self._nTFully  = nTFully
        self._nTested  = nTested
        self._testedAt = testedAt   # test locations
        if self._nTested is None:
            self._nTested = {}
            for aT in TESTS:
                self._nTested[aT] = 0
        # the end of base ini!

    @classmethod
    def fromJD(cls,jD):
        batch_name = jD["bName" ]
        ID         = jD["ID"    ]
        isReal     = jD["isReal"]
        Type       = jD["Type"  ]
        
        listWafers = []
        jWaf = jD["lWafers"]
        if jWaf is not None:
            for aW in jWaf:
                oWafer = Wafer.fromJD(aW)
                listWafers.append(oWafer)
        if len(listWafers) == 0:
            listWafers = None
            
        listMAINs = []
        jMAIN = jD["lMAINs"]
        if jMAIN is not None:
            for aM in jMAIN:
                oMAIN = MAIN.fromJD(aM)
                # Vf, 2021-10-18: don't think we need to do this -
                #         everything should be carbon-copied since the last eval
                #oTestData = aM["testData"]
                #oMAIN.fillTestData( oTestData )
                listMAINs.append(oMAIN)
        if len(listMAINs) == 0:
            listMAINs = None
            
        listHMs = []
        jHMs = jD["lHMs"]
        if jHMs is not None:
            for aHM in jHMs:
                oHM = HM.fromJD(aHM)
                listHMs.append(oHM)
        if len(listHMs) == 0:
            listHMs = None
            
        listQAchips = []
        jQAchips = jD["lQAchips"]
        if jQAchips is not None:
            for aQAchip in jQAchips:
                oQAchip = QAchip.fromJD(aQAchip)
                listQAchips.append(oQAchip)
        if len(listQAchips) == 0:
            listQAchips = None
            
        listQAminis = []
        jQAminis = jD["lQAminis"]
        if jQAminis is not None:
            for aQAmini in jQAminis:
                oQAmini = QAmini.fromJD(aQAmini)
                listQAminis.append(oQAmini)
        if len(listQAminis) == 0:
            listQAminis = None

        ifReturned = jD["ifReturned"]
        ifFailed   = jD["ifFailed"  ]
        qaTC       = jD["qaTC"      ]
        qaCCE      = jD["qaCCE"     ]
        nReady     = jD["nReady"    ]
        nUnhappy   = jD["nUnhappy"  ]
        nDamaged   = jD["nDamaged"  ]
        nPhantom   = jD["nPhantom"  ]
        nSpecial   = jD["nSpecial"  ]
        nReturned  = jD["nReturned" ]
        nTestOK  = jD["nTestOK" ]
        nUncert  = jD["nUncert" ]
        nTFully  = jD["nTFully" ]
        nTested  = jD["nTested" ]
        testedAt = jD["testedAt"]
        return cls( batch_name,
                    ID,
                    isReal,
                    Type,
                    listWafers,
                    listMAINs,
                    listHMs,
                    listQAminis,
                    listQAchips,
                    ifReturned, ifFailed, qaTC, qaCCE,
                    nReady,nUnhappy,nDamaged,nPhantom,nSpecial,nReturned,
                    nTestOK, nUncert, nTFully, nTested, testedAt )

    def toJD(self):
        listWafers = None
        if self.lWafers() is not None:
            listWafers = []
            for aW in self.lWafers():
                listWafers.append(aW.toJD())
        listMAINs = None
        if self.lMAINs() is not None:
            listMAINs = []
            for aM in self.lMAINs():
                listMAINs.append(aM.toJD())
        listHMs = None
        if self.lHMs() is not None:
            listHMs = []
            for aHM in self.lHMs():
                listHMs.append(aHM.toJD())
        listQAminis = None
        if self.lQAminis() is not None:
            listQAminis = []
            for aQAmini in self.lQAminis():
                listQAminis.append(aQAmini.toJD())
        listQAchips = None
        if self.lQAchips() is not None:
            listQAchips = []
            for aQAchip in self.lQAchips():
                listQAchips.append(aQAchip.toJD())
        outJD = { "bName"   : self._bName   ,
                  "ID"      : self._ID      ,
                  "isReal"  : self._isReal  ,
                  "Type"    : self._Type    ,
                  "lWafers" : listWafers    ,
                  "lMAINs"  : listMAINs     ,
                  "lHMs"    : listHMs       ,
                  "lQAminis": listQAminis   ,
                  "lQAchips": listQAchips   ,
                  "ifReturned": self._ifReturned,
                  "ifFailed"  : self._ifFailed  ,
                  "qaTC"      : self._qaTC      ,
                  "qaCCE"     : self._qaCCE     ,
                  "nReady"    : self._nReady    ,
                  "nUnhappy"  : self._nUnhappy  ,
                  "nDamaged"  : self._nDamaged  ,
                  "nPhantom"  : self._nPhantom  ,
                  "nSpecial"  : self._nSpecial  ,
                  "nReturned" : self._nReturned ,
                  "nTestOK" : self._nTestOK ,  
                  "nUncert" : self._nUncert , 
                  "nTFully" : self._nTFully ,
                  "nTested" : self._nTested ,
                  "testedAt": self._testedAt }
        return outJD

    def bName(self):
        return self._bName
    def ID(self):
        return self._ID
    def isReal(self):
        return self._isReal
    def Type(self):
        return self._Type
    def lWafers(self):
        return self._lWafers
    def lMAINs(self):
        return self._lMAINs
    def lHMs(self):
        return self._lHMs
    def lQAminis(self):
        return self._lQAminis
    def lQAchips(self):
        return self._lQAchips
    def testedAt(self):
        return self._testedAt

    def testedAtNice(self):
        retVal = (self._testedAt).replace("/","-")
        return retVal


    # codes for both MAIN sensors and Halfmoons
    def codesMainHM(self):
        retCodes = []
        for aS in self.lMAINs():
            retCodes.append(aS.code())
        for aH in self.lHMs():
            retCodes.append(aH.code())
        return retCodes

    # codes for both MAIN sensors and Halfmoons not in FS
    def codesMainHMconsider(self):
        retCodes = []
        lsnFS = []
        for aS in self.lMAINs():
            # don't want to rep-process the final ones
            if aS.stage() in FINAL_STATES:
                lsnFS.append( aS.SN() )
                continue
            retCodes.append(aS.code())
        for aH in self.lHMs():
            # skip halfmoon if the sensor SN is skipped
            theSN = makeSN_sensor( aH.SN() )
            if theSN in lsnFS:
                continue
            retCodes.append(aH.code())
        return retCodes

    # SNs for the MAIN sensors
    def SNsMain(self):
        retSNs = []
        for aS in self.lMAINs():
            retSNs.append(aS._SN)
        return retSNs
    
    # SNs for the MAIN sensors not in FS
    def SNsMainConsider(self):
        retSNs = []
        for aS in self.lMAINs():
            # don't want to rep-process the final ones
            if aS.stage() in FINAL_STATES:
                continue
            retSNs.append(aS._SN)
        return retSNs

    def nTotal(self):
        return ( len(self._lMAINs) )

    def ifReturned(self):
        return self._ifReturned
    def ifFailed(self):
        return self._ifFailed
    def qaTC(self):
        return self._qaTC
    def qaCCE(self):
        return self._qaCCE
    def nReady(self):
        return self._nReady
    def nUnhappy(self):
        return self._nUnhappy
    def nDamaged(self):
        return self._nDamaged
    def nPhantom(self):
        return self._nPhantom
    def nSpecial(self):
        return self._nSpecial
    def nReturned(self):
        return self._nReturned

    def sumFS(self):
        return ( self.nReady() +
                 self.nUnhappy() + self.nDamaged() +
                 self.nPhantom() +
                 self.nSpecial() + self.nReturned() )
    def isPartial(self):
        return ( self.sumFS() > 0 )
    def isFinal(self):
        return ( self.nTotal() == self.sumFS() )

    def nTotalCERN(self):
        nS = 0
        for aS in self._lMAINs:
            if aS._ordPath == 'CERN':
                nS += 1
        return nS

    def nTotalKEK(self):
        nS = 0
        for aS in self._lMAINs:
            if aS._ordPath == 'KEK':
                nS += 1
        return nS

    def nWarranty(self):
        nW = 0
        for aS in self._lMAINs:
            wFlag = aS.warFlag()
            if wFlag is not None:
                if wFlag:
                    nW += 1
        return nW

    def toApprove(self):
        retV = False
        for aS in self._lMAINs:
            if aS._stage == "BLESSING":
                retV = True
                break
        return retV


    def fillTestData(self, dictData):
        logFTD = logging.getLogger('LOG-FTD')

        # add info
        success = True
        for snD in dictData:
            found = False
            for aSensor in self.lMAINs():
                if snD == aSensor.SN() :
                    # Don't want to check for it -
                    #    it's a higher-level "forced" decision!
                    # and
                    # not aSensor.stage() in FINAL_STATES ):
                    aSensor.fillTestData( dictData[snD] )
                    self.fillTestedAt( dictData[snD]["testedAt"] )
                    found = True
            if not found:
                logFTD.error(" did not find SN = <" + snD + ">")
                success = False

        self.evaluateBatch()

        return success


    def updateBadness(self,inDict):
        K = 'batches'
        useDict = {}
        if K in inDict:
            useDict = inDict[K]
        else:
            return
        bN = self.bName()
        if bN in useDict:
            if "ifReturned" in useDict[bN]:
                self._ifReturned = useDict[bN]["ifReturned"]
            if "ifFailed" in useDict[bN]:
                self._ifFailed = useDict[bN]["ifFailed"]

        # VF, 2021-10-18:
        #   we dont' re-evaluate here. But might want to do in the future!
        return
    
        
    def updateQA(self,qaTC,qaCCE):
        if qaTC is None and qaCCE is None:
            return
        if qaTC is not None:
            self._qaTC = qaTC
        if qaCCE is not None:
            self._qaCCE = qaCCE
        # now go over the sensors
        for S in self.lMAINs():
            S.updateQA(qaTC,qaCCE)
        self.evaluateBatch()
        return


    def updateSensorControl(self,inDict):
        to_update = False
        # check if have the info to work with
        K = 'sensors'
        useDict = {}
        if K in inDict:
            useDict = inDict[K]
        else:
            return
        # scan sensors and the dictionary
        for S in self.lMAINs():
            sn = S.SN()
            if sn in useDict:
                cInfo = useDict[sn]
                S.update_owData(cInfo)
                to_update = True
        # re-evaluate the batch, if appropriate
        if to_update:
            self.evaluateBatch()
        return


    def evaluateBatch(self):
        logging.getLogger()
        # re-parse the data to update the service information
        statTested     = {}
        statTestedCERN = {}
        statTestedKEK  = {}
        for aT in TESTS:
            statTested[aT]     = 0
            statTestedCERN[aT] = 0
            statTestedKEK[aT]  = 0
        self._nReady    = 0
        self._nUnhappy  = 0
        self._nDamaged  = 0
        self._nPhantom  = 0
        self._nSpecial  = 0
        self._nReturned = 0
        self._nTestOK = 0
        self._nUncert = 0
        self._nTFully = 0
        for S in self.lMAINs():

            # fill in the statistics
            for aT in TESTS:
                if S.flatT(aT) is not None:
                    statTested[aT] += 1
                    if S._ordPath == "CERN":
                        statTestedCERN[aT] += 1
                    elif S._ordPath == "KEK":
                        statTestedKEK[aT] += 1
                    else:
                        logging.error(" Illegal order path! Something is seriously wrong!!!!")
                # if have data
            # loop over tests

            # increment the final state counts
            self.increment_FS_counts( S.stage() )

            # the global numbers
            if S._TestsOK:
                self._nTestOK += 1
            if S._TestsUncert:
                self._nUncert += 1
            if S._FullyTested:
                self._nTFully += 1
        # end loop over sensors
        self._nTested = statTested

        nSensCERN = self.nTotalCERN()
        nSensKEK  = self.nTotalKEK()
        coverTst     = {}
        coverTstCERN = {}
        coverTstKEK  = {}
        CONSIDER_TESTS = NEED_ALL_IDs + ['stabID','fullstripID','thickID']
        for aT in CONSIDER_TESTS:
            coverTst[aT]     = False
            coverTstCERN[aT] = False if nSensCERN>0 else True
            coverTstKEK[aT]  = False if nSensKEK >0 else True
        #coverTst['stabID'     ] = False
        #coverTst['fullstripID'] = False
        #coverTst['thickID'    ] = False
        if nSensCERN > 0:
            # full converage
            for aT in NEED_ALL_IDs:
                if statTestedCERN[aT] == nSensCERN:
                    coverTstCERN[aT] = True
            # fractionals
            frac = statTestedCERN['stabID'] / nSensCERN
            if frac >= 0.10:
                coverTstCERN['stabID'] = True
            frac = statTestedCERN['fullstripID'] / nSensCERN
            if frac >= 0.02:
                coverTstCERN['fullstripID'] = True
            if statTestedCERN['thickID'] > 0:
                coverTstCERN['thickID'] = True

        if nSensKEK > 0:
            # full coverage
            for aT in NEED_ALL_IDs_KEK:
                if statTestedKEK[aT] == nSensKEK:
                    coverTstKEK[aT] = True
            # fractionals
            for aT in ['inspecID','ivID','stabID']:
                frac = statTestedKEK[aT] / nSensKEK
                if frac >= 0.10:
                    coverTstKEK[aT] = True
            if statTestedKEK['thickID'] > 0:
                coverTstKEK['thickID'] = True
            # completely artificial -- these tests are not done
            for aT in ['cvID','fullstripID']:
                coverTstKEK[aT] = True

        # combine them for the batch consideration purposes
        for aT in CONSIDER_TESTS:
            coverTst[aT] = coverTstCERN[aT] and coverTstKEK[aT]

        # add the warranty wafer existence check
        coverTst['warFlag'] = bool( self.nWarranty() > 0 )

        self._coverage = coverTst

        return


    def increment_FS_counts(self, stage):
        if stage == "READY_FOR_MODULE":
            self._nReady    += 1
        if stage == "UNHAPPY":
            self._nUnhappy  += 1
        if stage == "DAMAGED":
            self._nDamaged  += 1
        if stage == "PHANTOM":
            self._nPhantom  += 1
        if stage == "SPECIAL_USE":
            self._nSpecial  += 1
        if stage == "RETURNED":
            self._nReturned += 1
        return


    def decrement_FS_counts(self, stage):
        if stage == "READY_FOR_MODULE":
            self._nReady    -= 1
        if stage == "UNHAPPY":
            self._nUnhappy  -= 1
        if stage == "DAMAGED":
            self._nDamaged  -= 1
        if stage == "PHANTOM":
            self._nPhantom  -= 1
        if stage == "SPECIAL_USE":
            self._nSpecial  -= 1
        if stage == "RETURNED":
            self._nReturned -= 1
        return


    def update_counts(self,sn):
        for S in self.lMAINs():
            # find the sensor
            if S.SN() == sn:
                # find its states
                stateNow = S.stage()
                stateNxt = S._approval["FINALSTAGE"]
                # change the state
                S._stage = stateNxt
                # change the counts
                self.increment_FS_counts(stateNxt)
                self.decrement_FS_counts(stateNow)
        return
            
    def fillTestedAt(self, aLoc ):
        if aLoc is None:
            return
        # fill in if first time, otherwise add
        if len(self._testedAt) == 0:
            self._testedAt = aLoc
        else:
            sites = aLoc.split("/")
            for aSite in sites:
                if aSite not in self._testedAt:
                    self._testedAt += "/" + aSite
            # end loop of featured sites
        return


    def html_table_sensor_status(self):

        # now, start printing....
        hT = ""
        hT += "<table>\n"
        hT += ( "<caption> Sensor status for batch <b>" + str(self._bName) + "</b>" +
                ", tested at <b>" + self.testedAt() + "</b>" +
                ", design version = " + DESIGN +  
                "</caption>\n" )
        hT += "<tbody>\n"

        TESTS = NEED_ALL_IDs + NEED_SAMPLE_IDs + NEED_TODO_IDs

        # header
        hT += '  <tr>\n'
        #   1) SN + warranty
        hT += self.html_head_cell("SN")
        hT += self.html_head_cell("warFlag")
        #   2) the tests
        for aK in TESTS:
            hT += self.html_head_cell(aK)
        #   3) the summary columns
        lSumm = ['AllTests','TestsOK','Uncert.','QA-TC','QA-CCE','Destination','Notes']
        for aC in lSumm:
            hT += self.html_head_cell(aC)
        hT += '  </tr>\n'

        for S in self._lMAINs:
            hT += '  <tr>\n'
            # 1) SN + warranty
            hT += self.html_link_object(S.SN(), S.code())
            hT += self.html_show_warranty(S.warFlag())
            # 2) the tests
            for aT in TESTS:
                hT += S.html_test_status(aT)
            # 3) the summary columns
            hT += self.html_color_status(S._FullyTested,"",  cPink)
            hT += self.html_color_status(S._TestsOK    ,"",  cRed )
            hT += self.html_color_status(S._TestsUncert,cYellow, "" )
            hT += self.html_color_bool(S._QATC)
            hT += self.html_color_bool(S._QACCE)
            hT += self.html_destination( S._Destination, S.stage() )
            hT += self.html_show_str(S._Notes )
            # end-note for the sensor
            hT += '  </tr>\n'

        # And now, we'll add the statistics:
        #   Totals
        nSens = self.nTotal()
        hT += '  <tr>\n'
        hT += self.html_show_str('Total') # SN column
        hT += self.html_show_num( nSens ) # warranty column
        for aT in TESTS:
            hT += self.html_show_num( nSens )
        for aC in lSumm:
            hT += self.html_show_num( nSens )
        hT += '  </tr>\n'
        #   N(tested):
        hT += '  <tr>\n'
        hT += self.html_show_str('Tested')
        hT += self.html_show_num( self.nWarranty(),'warFlag' )
        for aT in TESTS:
            hT += self.html_show_num( self._nTested[aT], aT )
        hT += self.html_show_num( self._nTFully )
        hT += self.html_show_num( self._nTestOK )
        hT += self.html_show_num( self._nUncert )
        for i in range(2):
            hT += self.html_show_str(' ')
        hT += self.html_show_num( self.sumFS() )
        hT += self.html_show_str(' ')
        hT += '  </tr>\n'

        hT += "</tbody>\n"
        hT += "</table>\n"
        return hT


    def html_summary(self):
        hT = ""
        hT += "<HTML> \n"
        hT += "<HEAD> \n"
        hT += "<TITLE> Summary for batch " + str(self._bName) + " </TITLE> \n"
        hT += "</HEAD> \n"
        hT += "<BODY> \n"

        # the batch summary
        hT += self.html_table_sensor_status()

        hT += "<br><br>"

        # detailed summary for sensors
        hT += self.html_table_sensor_parameters()

        hT += "</BODY> \n"
        hT += "</HTML> \n"


        return hT


    def html_table_sensor_parameters(self):
        # now, start printing....
        hT = ""
        hT += "<table>\n"
        hT += ( "<caption> Sensor parameter summary for batch <b>" + str(self._bName) + "</b>" +
                ", tested at <b>" + self.testedAt() + "</b>" +
                ", design version = " + DESIGN +  
                "</caption>\n" )
        hT += "<tbody>\n"

        # header
        hT += '  <tr>\n'
        for aK in TABLE_KEYS:
            if aK.endswith("Pass") or aK == "code" or aK == "ivDate":
                continue
            hT += self.html_head_cell(aK)
        hT += '  </tr>\n'

        # rest of the body
        for S in self._lMAINs:
            hT += '  <tr>\n'
            for aK in TABLE_KEYS:
                if aK.endswith("Pass") or aK == "code" or aK == "ivDate":
                    continue
                val = S.flatT(aK)
                # either formatted link or the "numbers"
                if aK.endswith("ID"):
                    # figure out if we want to flag it
                    passName = aK[:-2] + "Pass"
                    toFlag = S.flatT(passName)
                    necessary = S.needed_test(aK)
                    hT += self.html_link_test(val,toFlag,necessary)
                elif aK == "SN":
                    hT += self.html_link_object(S.SN(), S.code()) #val, S.flatT("code"))
                elif aK == "warFlag":
                    hT += self.html_show_warranty(S.warFlag())
                else:
                    hT += S.html_variable(val,aK)
            hT += '  </tr>\n'

        hT += "</tbody>\n"
        hT += "</table>\n"
        return hT


    def html_link_test(self,val,passFlag, necessary):
        #<a href="http://example.com">anchored text</a>
        cColor = "" # the cell color, in case we want to highlight it
        if passFlag is None:
            # To flat the test as missing, if it's necessary
            if necessary:
                cColor = cPink
        else:
            # To flag the test as red if it's marked as failed
            if not passFlag:
                cColor = cRed
        retV = ""
        retV += '  <td' + cColor + '>'

        if val is not None:
            # since the strip test is a list of things, will make everything a list
            if not ( type(val) is list ):
                val = [val]
            many = True if len(val) > 1 else False
            for i,ref in enumerate(val):
                Li = 'L' + str(i+1) if many else 'Link'
                retV += '<a href=\"' + html_pref_test_ + str(ref) + '\">' + Li + '</a>'
                if many and i+1 < len(val):
                    retV += ','
            #retV += '<a href=\"' + html_pref_test_ + str(val) + '\">Link</a>'

        retV += '  </td>'
        return retV


    def html_link_object(self,SN,code):
        #<a href="http://example.com">anchored text</a>
        retV = ""
        retV += '  <td>'
        retV += '<a href=\"' + html_pref_obj_ + str(code) + '\">' + str(SN) + '</a>'
        retV += '  </td>'
        return retV


    def html_head_cell(self,inS):
        useS = inS
        # nicer header labels
        if useS in HEAD_CASE:
            useS = HEAD_CASE[useS]
        retV = ""
        retV += '  <td>'
        retV += "<b>" + str(useS) + "</b>"
        retV += '  </td>'
        return retV


    def html_color_status(self,Good,cTrue="",cFalse=""):
        nColor = cTrue
        aWord = "Yes"
        if not Good:
            nColor = cFalse
            aWord = "No"
        retV = ""
        retV += '  <td' + nColor + '>'
        retV += aWord
        retV += '  </td>'
        return retV


    def html_destination(self, destiny, state):
        nColor = ''
        if state in FINAL_STATES:
            inp = state
            inp_show = "<b>" + state + "</b>"
        else:
            inp = destiny
            inp_show = destiny
            
        if inp == 'READY_FOR_MODULE':
            nColor = cGreen
        elif inp == 'UNHAPPY' or inp == 'DAMAGED':
            nColor = cRed
        elif inp == 'SPECIAL_USE':
            nColor = cPink
        retV = ""
        retV += '  <td' + nColor + '>'
        retV += inp_show
        retV += '  </td>'
        return retV


    def html_show_num(self, num, aT=""):
        nColor = ""
        if len(aT)>0:
            if aT in self._coverage:
                if self._coverage[aT]:
                    nColor = cGreen
                else:
                    nColor = cPink
        retV = ""
        retV += '  <td ' + nColor + ' align=\"right\" >'
        retV += str(num)
        retV += '  </td>'
        return retV
        

    def html_show_str(self, aStr):
        retV = ""
        retV += '  <td>'
        retV += aStr
        retV += '  </td>'
        return retV
        

    def html_color_bool(self, aFlag):
        retV = ""
        showS = ""
        nColor = ""
        if aFlag is not None:
            if aFlag:
                showS = "Pass"
                nColor = cGreen
            else:
                showS = "Fail"
                nColor = cRed
        retV += '  <td' + nColor + '>'
        retV += showS
        retV += '  </td>'
        return retV
        

    def html_show_warranty(self, wFlag):
        retV = ""
        showS = ""
        nColor = ""
        if wFlag is not None:
            if wFlag:
                showS = "Yes"
        else:
            showS = "N/A"
            nColor = cRed
        retV += '  <td' + nColor + '>'
        retV += showS
        retV += '  </td>'
        return retV
        

    def sensor_type(self,theSN):
        for aS in self._lMAINs:
            if aS._SN == theSN:
                return aS._Type
        # should not get here
        return "Not Defined"


    def short_status_table(self):
        table = []
        table.append( ["SN","Destination","Comment"] )
        for S in self.lMAINs():
            table.append( [S.SN(), S._Destination, S._Notes] )
        ret_status = tabulate(table, headers = "firstrow", tablefmt = "psql")
        return ret_status

    
#____________________________
class Wafer():
    def __init__(self,SN,code):
        self._SN   = SN
        self._code = code

    @classmethod
    def fromJD(cls,jD):
        SN   = jD["SN"  ]
        code = jD["code"]
        return cls(SN,code)

    def toJD(self):
        outJD = { "SN" : self._SN, "code" : self._code }
        return outJD

    def SN(self):
        return self._SN
    def code(self):
        return self._code


#____________________________
class MAIN():
    def __init__(self,SN,code,ID,sType,receptionDate,ordPath,warFlag,stage,locationQC,
                 QATC=None,QACCE=None,owDATA=None,
                 testData=None, qualData=None, flatT=None, approval=None, recAccept=None,
                 TestsOK=True, TestsUncert=False, FullyTested=False, Destination="", Notes=""):
        self._SN      = SN
        self._code    = code
        self._ID      = ID
        self._Type    = sType
        self._rDate   = receptionDate
        self._ordPath = ordPath
        self._warFlag = warFlag
        self._stage   = stage
        self._locQC   = locationQC
        self._QATC     = QATC
        self._QACCE    = QACCE
        self._owData   = owDATA    # data dict
        self._testData = testData  # data dict
        self._qualData = qualData  # data dict
        self._flatT    = flatT     # data dict
        self._approval  = approval  # data dict
        self._recAccept = recAccept # data dict
        self._TestsOK     = TestsOK
        self._TestsUncert = TestsUncert
        self._FullyTested = FullyTested
        self._Destination = Destination
        self._Notes       = Notes

    @classmethod
    def fromJD(cls,jD):
        SN      = jD["SN"     ]
        code    = jD["code"   ]
        ID      = jD["ID"     ]
        Type    = jD["Type"   ]
        rDate   = jD["rDate"  ]
        ordPath = jD["ordPath"]
        warFlag = jD["warFlag"]
        stage   = jD["stage"  ]
        locQC   = jD["locQC"  ]
        QATC     = jD["QATC"  ]
        QACCE    = jD["QACCE" ]
        owData   = jD["owData"]
        testData = jD["testData"   ]
        qualData = jD["qualData"   ]
        flatT    = jD["flatT"      ]
        approval  = jD["approval"  ]
        recAccept = jD["recAccept" ]
        TestsOK     = jD["TestsOK"    ]
        TestsUncert = jD["TestsUncert"]
        FullyTested = jD["FullyTested"]
        Destination = jD["Destination"]
        Notes       = jD["Notes"      ]
        return cls(SN, code, ID, Type, rDate, ordPath, warFlag, stage, locQC,
                   QATC, QACCE, owData,
                   testData, qualData, flatT, approval, recAccept,
                   TestsOK, TestsUncert, FullyTested, Destination, Notes)

    def toJD(self):
        outJD = { "SN"          : self._SN         ,
                  "code"        : self._code       ,
                  "ID"          : self._ID         ,
                  "Type"        : self._Type       ,
                  "rDate"       : self._rDate      ,
                  "ordPath"     : self._ordPath    ,
                  "warFlag"     : self._warFlag    ,
                  "stage"       : self._stage      ,
                  "locQC"       : self._locQC      ,
                  "QATC"        : self._QATC       ,
                  "QACCE"       : self._QACCE      ,
                  "owData"      : self._owData     ,
                  "testData"    : self._testData   ,
                  "qualData"    : self._qualData   ,
                  "flatT"       : self._flatT      ,
                  "approval"    : self._approval   ,
                  "recAccept"   : self._recAccept  ,
                  "TestsOK"     : self._TestsOK    ,
                  "TestsUncert" : self._TestsUncert,
                  "FullyTested" : self._FullyTested,
                  "Destination" : self._Destination,
                  "Notes"       : self._Notes }
        return outJD

    def SN(self):
        return self._SN
    def code(self):
        return self._code
    def ID(self):
        return self._ID
    def Type(self):
        return self._Type
    def rDate(self):
        return self._rDate
    def warFlag(self):
        return self._warFlag
    def stage(self):
        return self._stage
    def locQC(self):
        return self._locQC
    def testData(self):
        return self._testData
    def qualData(self,K):
        return self._qualData[K]
    
    def finalQualData(self,K):
        # if we have the overwrite data, use those
        if self._owData is not None:
            if K in self._owData:
                if self._owData[K] is not None:
                    return self._owData[K]
        # otherwise, use the regular qualData
        return self._qualData[K]
    
    def flatT(self,K):
        if self._flatT is None:
            return None
        if K in ["fullstripPass", "kekPass"]:
            # anticipate this to be None or a list
            V = self._flatT[K]
            return self.composite_bool(V)
        else:
            return self._flatT[K]
        
    def finalFlatT(self,K):
        # if we have the overwrite data, use those
        if self._owData is not None:
            if K in self._owData:
                if self._owData[K] is not None:
                    return self._owData[K]
        # otherwise, use the regular "flattened" DB data
        return self.flatT(K)

    def consistent(self,K):
        # if we have the overwrite data,
        # that removes the apparent inconsistencies
        if self._owData is not None:
            if K in self._owData:
                if self._owData[K] is not None:
                    return True
        # otherwise, compare the parameter checks and the DB
        goodParams = self.qualData(K)
        goodDB     = self.flatT(K)
        return (goodParams == goodDB)

    def composite_bool(self,V):
        if V is None:
            return V
        else:
            # to AND all the values
            if type(V) is list:
                retV = True
                for el in V:
                    retV = retV and el
                return retV
            else:
                return V

    def owDestination(self):
        K = "Destination"
        if self._owData is None:
            return None
        if not K in self._owData:
            return None
        else:
            return self._owData[K]

    def fillTestData(self,dictData):
        # copy incoming data
        self._testData = dictData
        # make the table convenient to use
        self._testData["SN"     ] = self._SN
        self._testData["code"   ] = self._code
        self._testData["rDate"  ] = self._rDate
        self._testData["ordPath"] = self._ordPath
        self._testData["warFlag"] = self._warFlag
        self._testData["stage"  ] = self._stage
        self._testData["site"   ] = self._locQC
        self._testData["QATC"   ] = self._QATC
        self._testData["QACCE"  ] = self._QACCE

        self.makeFlatT()
        self.evaluateSensor()

        return

    
    def updateQA(self,iqaTC,iqaCCE):
        self._QATC = iqaTC
        self._QACCE = iqaCCE
        self.evaluateSensor()
        return
    

    def update_owData(self,owData):
        self._owData = owData
        self.evaluateSensor()
        return

    
    def evaluateSensor(self):
        # don't do that for the ones that arrived
        if self.stage() in FINAL_STATES:
            return
        
        # reset our notes before the next evaluation, etc
        self._Notes = ""
        # report the forceful conclusions
        if self._owData is not None:
            for K in self._owData:
                self.add_note( "OW-" + K + ":" + str(self._owData[K]) )

        # No data for this one, but would like to add a note!
        if self.flatT('inspecID') is not None:
            if not self.flatT('inspecPass'):
                symptom = "fail"
                if self.flatT('inspecDmg') is not None:
                    symptom = self.flatT('inspecDmg')
                self.add_note( HEAD_CASE['inspecID'] + ": " + symptom )

        # now, parse the data and fill in the service information
        self.evalData()

        # check if all necessary tests are there!
        fullyTested = True
        if self._ordPath == 'CERN':
            for aT in NEED_ALL_IDs:
                if self.flatT(aT) is None:
                    fullyTested = False
                    self.add_note((HEAD_CASE[aT] + ": missing"))
        elif self._ordPath == 'KEK':
            for aT in NEED_ALL_IDs_KEK:
                if self.flatT(aT) is None:
                    fullyTested = False
                    self.add_note((HEAD_CASE[aT] + ": missing"))
        self._FullyTested = fullyTested

        # check if all tests that are done are good
        # (according to parameters for the ones with data)
        testsOK     = True
        testsUncert = False
        for aT in TESTS:
            if self.flatT(aT) is not None:
                passName = aT[:-2] + "Pass"
                goodParams = self.finalQualData(passName) #self.qualData(passName)
                if not goodParams:
                    testsOK = False
                if not self.consistent(passName):
                    testsUncert = True
                    '''
                goodEval = self.flatT(passName)
                if goodEval != goodParams:
                    testsUncert = True
                    '''
        # just in case
        if self.flatT('handleID') is not None:
            if not self.flatT('handlePass'):
                testsOK = False
                self.add_note( (HEAD_CASE['handleID'] + ": damage") )
        if self.flatT('specUseID') is not None:
            self.add_note( (HEAD_CASE['specUseID'] ) )

        self._TestsOK     = testsOK
        self._TestsUncert = testsUncert
        # make the destination theme
        destination = "N/A"
        # use the over-write decision, if available
        owDestiny = self.owDestination()
        if owDestiny is not None:
            destination = owDestiny
        else:
            if self.flatT('specUseID') is not None:
                destination = 'SPECIAL_USE'
            elif ( self.flatT('handleID') is not None and
                   self.flatT('handlePass') is False ):
                destination = 'DAMAGED'
            elif testsUncert:
                destination = '-- to-recheck --'
            elif testsOK:
                destination = 'READY_FOR_MODULE'
            else:
                destination = 'UNHAPPY'
        # care for the QA status
        for qaFlag in [self._QATC, self._QACCE]:
            if qaFlag is not None:
                if not qaFlag and destination == 'READY_FOR_MODULE':
                    destination = 'UNHAPPY'
                    self.add_note("QA problem")
        self._Destination = destination

        return


    def makeFlatT(self):
        # the SN data
        self._flatT = {}
        for N in ["SN", "code", "rDate", "ordPath", "warFlag", "stage", "site"]:
            self._flatT[N] = self._testData[N]

        # loop over TABLE_KEYS
        for aKey in TABLE_KEYS:
            # these data were added above
            if aKey in ADD_KEYS:
                continue
            # if in MERGE_KEYS, care
            if aKey in MERGE_KEYS:
                lSubKeys = MERGE_KEYS[aKey]
                if aKey == 'inspecDmg':
                    combV = None
                    for sK in lSubKeys:
                        locV = self._testData[sK]
                        if locV is None:
                            continue
                        if len(locV.strip())==0:
                            continue
                        if combV is None:
                            combV = locV
                        else:
                            combV += " + " + locV
                    # end of sub-key loop
                    self._flatT[aKey] = combV
                # end of inspection combinations
            else:
                # otherwise just fill in
                self._flatT[aKey] = self._testData[aKey]
        # end data parsing
        return
    

    def evalData(self):
        # initialization
        self._qualData = {}
        for aK in self._testData:
            self._qualData[aK] = True

        # copy over the non-data test results
        self._qualData['inspecPass' ] = self._testData['inspecPass' ]
        self._qualData['kekPass'    ] = self.composite_bool(self._testData['kekPass'])
        self._qualData['handlePass' ] = self._testData['handlePass' ]
        self._qualData['recovPass'  ] = self._testData['recovPass'  ]
        self._qualData['specUsePass'] = self._testData['specUsePass']

        # but to check if the data are present - otherwise flag the *IDs as False
        for aK in self._testData:
            if aK.endswith("ID"):
                if self._testData[aK] is None:
                    self._qualData[aK] = False

        # evaluate the params for the rest
        # HPK test
        for N in ['hpkVfd','hpkI500V','hpkVbd','hpkMaxNBad','hpkBadPerc']:
            self.evaluate_param(N,'hpkPass')
        # ATLAS IV
        for N in ['I500V','Vbd']:
            self.evaluate_param(N,'ivPass')
        # ATLAS CV
        for N in ['Vfd','actThick']:
            self.evaluate_param(N,'cvPass')
        # Stability
        for N in ['stabIleak','stabIvar']:
            self.evaluate_param(N,'stabPass')
        # Strip
        for N in ['atlNbadSeq','atlNbadFrac']:
            self.evaluate_param(N,'fullstripPass')
        # Shape
        for N in ['Bow']:
            self.evaluate_param(N,'shapePass')
        for N in ['TH']:
            self.evaluate_param(N,'thickPass')
        # check the passes...


    def evaluate_param(self,N, test, dbg=False):
        logEP_ = logging.getLogger('LOG-EP_')

        d = self._testData[N]
        if type(d) is list:
            if len(d) == 0:
                return
        else:
            # make it a list to iterate later
            d = [d]

        for i,v in enumerate(d):
            if v is not None:
                # we have data written as percentage...
                if not isinstance(v,numbers.Number):
                    v = float(v.strip('%'))

                Lim = LIMITS[N]['val']
                OP  = LIMITS[N]['oper']
                # tolerance around central value
                if 'cval' in LIMITS[N]:
                    v = abs( v - LIMITS[N]['cval'] )
                if dbg:
                    print(" Lim = " + str(Lim) + ", oper = " + str(OP) + ", value = " + str(v))
                Compl = True
                if OP == 'less':
                    Compl = ( v <  Lim )
                elif OP == 'leeq':
                    Compl = ( v <= Lim )
                elif OP == 'more':
                    Compl = ( v >  Lim )
                elif OP == 'moeq':
                    Compl = ( v >= Lim )
                if not Compl:
                    self._qualData[N   ] = False
                    self._qualData[test] = False
                    self.add_note( ( HEAD_CASE[test.replace('Pass','ID')] + ": " + N + " failed" ) )

                if dbg:
                    print("SN = " + self._SN + " Compliance = " + str(Compl))

                # correct special cases... just because we have the weird features in our data
                if N == 'Vbd' and test == 'ivPass':
                    if i>0:
                        logEP_.error(" expected only 1 IV test! Exiting")
                        return
                    vmax = 0.0
                    lVolts = self._testData['atliv_v']
                    # these things might be negative.... => an explicit scan
                    if lVolts is not None:
                        for aV in lVolts:
                            if abs(aV) > vmax:
                                vmax = abs(aV)
                    if ( abs(v-500.0) < 1.0 and abs(vmax-500.0) < 1.0 ):
                        self._qualData[N   ] = True
                        self._qualData[test] = True
                        self.add_note("IV: reset Vbd flag")
                        logEP_.info("  correcting {}/{}, v = {:.3f}, vmax = {:.3f}".format(N,test,v,vmax) )
                if N == 'Vfd' and test == 'cvPass':
                    if i>0:
                        logEP_.error(" expected only 1 CV test! Exiting")
                        return
                    if v > 350.0 and v < Lim:
                        self._qualData[N   ] = True
                        self._qualData[test] = True
                        self._flatT[test]    = True # this is unusual, but will reset the DB test flag
                        self.add_note("CV: reset Vfd flag")
                        logEP_.info("  correcting {}/{}, v = {:.3f}".format(N,test,v) )
            # check if v is None
        # loop over the list values
        return
        

    def html_variable(self,val,name):
        useV = val
        if val is not None:
            if not isinstance(val,numbers.Number):
                if name in ["atlNbadFrac"]:
                    # decompose the list and add formatted strings
                    useV = []
                    for el in val:
                        if el is None:
                            useV.append(str(el))
                        else:
                            useV.append(f'{el:.4f}')
                    # loop over the list
                    useV = str(useV)
                else:
                    # had lists (?!) in some early strangenesses
                    # and now for the updated strip tests - a combination of tests
                    useV = str(val)
                    # rename the long words
                    if name == "stage":
                        if useV == "SENS_TEST_STAGE":
                            useV = "QC"
                        elif useV == "BLESSING":
                            useV = "Bless"
                    if name == "site":
                        useV = useV.replace("UCSC_STRIP_SENSORS","SCIPP")
            else:
                if name in ["hpkVfd","hpkVbd","Vbd","Vfd",
                            "actThick","stabIleak","Bow","hpkMaxNBad"]:
                    useV = f'{val:.0f}'
                if name in ["hpkI500V","I500V","Neff","stabIvar"]:
                    useV = f'{val:.3f}'
                if name in ["RMS700V","hpkBadPerc"]:
                    useV = f'{val:.4f}'
        else:
            useV = ""
        # the right-alighment for numbers
        rAlign = ''
        if isinstance(val,numbers.Number):
            rAlign += ' align=\"right\"'
        # highlight the out-of-spec numbers
        nColor = ''
        if self._qualData is not None:
            if name in self._qualData:
                if self._qualData[name] is not None:
                    if not self._qualData[name]:
                        nColor += cRed
        retV = ""
        retV += '  <td' + rAlign + nColor + '>'
        retV += str(useV)
        retV += '  </td>'
        return retV


    def html_test_status(self,aT):
        retV = ""
        classColor = ""
        classWord  = " "

        passName = aT[:-2] + "Pass"
        ##goodParams = self.qualData(passName)
        #goodEval   = self.flatT(passName)
        goodEval   = self.finalFlatT(passName)
        
        refTest = self.flatT(aT)
        if refTest is None:
            # missing, but needed
            if self.needed_test(aT):
                classColor = cPink
                classWord  = "Miss"
        else:
            # questionable
            if not self.consistent(passName): #goodEval != goodParams:
                classColor = cYellow
                classWord  = "?"
            elif goodEval:
                classColor = cGreen
                classWord  = "OK"
            else:
                classColor = cRed
                classWord  = "Bad"

        retV += '  <td' + classColor + '>'
        retV += classWord
        retV += '  </td>'


        return retV


    def needed_test(self,aT):
        retV = False
        if ( ( self._ordPath == 'CERN' and aT in NEED_ALL_IDs ) or
             ( self._ordPath == 'KEK'  and aT in NEED_ALL_IDs_KEK ) ):
            retV = True
        return retV


    def add_note(self,inp):
        # will add the message to the Notes if it's not there yet
        if not inp in self._Notes:
            # will add the "/" separator if something is there already
            if len(self._Notes) > 0:
                self._Notes += " / "
            self._Notes += inp
        return


    def recAccept_json(self,inDate):
        outJson = self.test_json("ATLAS18_RECACCEPT_V1",inDate)
        self._recAccept = outJson
        return outJson


    def approval_json(self,inDate):
        outJson = self.test_json("ATLAS18_APPROVAL_V1",inDate)
        self._acceptance = outJson
        return outJson

    
    # for the tests, have the choices of
    # a) testData - as per the test flag in DB
    # b) flatT    - the "flattened" version with different test versions combined
    #               this is what's usually used; for Vbd just above 350 V it's reset
    # c) qualData - as per our test parameters evaluation
    # ==> Will use flatT, except for pass, where qualData combined with owData is the answer.
    def test_json(self,testName, inDate):
        test_passed = (
            ( self._Destination == "READY_FOR_MODULE" ) or
            ( self._Destination == "SPECIAL_USE" and self._TestsOK )
        )
        outJSON = {
            "component"  : self.code(),
            "testType"   : testName,
            "institution": self._ordPath,
            "runNumber"  : "1",  # to update it at some point???
            "date"       : inDate, #"2021-10-16T03:50:31.275Z",
            "passed"     : test_passed,
            "problems"   : (not test_passed),
            "results": {
                "RDATE"         : self.rDate(),
                "GOLDEN_WAFER"  : self.warFlag(),
                "TESTED_AT"     : self.flatT('testedAt'),
                "HPKID"         : self.flatT('kekID'),
                "HPKPASS"       : self.finalQualData('kekPass'),
                "INGOT"         : self.flatT('ingot'),
                "HPKVFD"        : self.flatT('hpkVfd'),
                "HPKMAXNBAD"    : self.flatT('hpkMaxNBad'),
                "HPKBADPERC"    : self.flatT('hpkBadPerc'),
                "INSPECID"      : self.flatT('inspecID'),
                "INSPECPASS"    : self.finalQualData('inspecPass'),
                "INSPECDMG"     : self.flatT('inspecDmg'),
                "IVID"          : self.flatT('ivID'),
                "IVPASS"        : self.finalQualData('ivPass'),
                "I500V"         : self.flatT('I500V'),
                "VBD"           : self.flatT('Vbd'),
                "RMS700V"       : self.flatT('RMS700V'),
                "CVID"          : self.flatT('cvID'),
                "CVPASS"        : self.finalQualData('cvPass'),
                "VFD"           : self.flatT('Vfd'),
                "NEFF"          : self.flatT('Neff'),
                "ACTTHICK"      : self.flatT('actThick'),
                "STABID"        : self.flatT('stabID'),
                "STABPASS"      : self.finalQualData('stabPass'),
                "STABILEAK"     : self.flatT('stabIleak'),
                "STABIVAR"      : self.flatT('stabIvar'),
                "FULLSTRIPID"   : self.flatT('fullStripID'), # array
                "FULLSTRIPPASS" : self.finalQualData('fullStripPass'), # single boolean
                "SEGMENTNO"     : self.flatT('segmentNo'),     # array
                "ATLNBADSEQ"    : self.flatT('atlNbadSeq'),    # array
                "ATLNBADFRAC"   : self.flatT('atlNbadFrac'),   # array
                "SHAPEID"       : self.flatT('shapeID'),
                "SHAPEPASS"     : self.finalQualData('shapePass'),
                "BOW"           : self.flatT('Bow'),
                "THICKID"       : self.flatT('thickID'),
                "THICKPASS"     : self.finalQualData('thickPass'),
                "TH"            : self.flatT('TH'),
                "KEKID"         : self.flatT('kekID'),         # array
                "KEKPASS"       : self.finalQualData('kekPass'), # single boolean
                "KEKSEGNO"      : self.flatT('kekSegNo'),      # array
                "HANDLEID"      : self.flatT('handleID'),
                "HANDLEPASS"    : self.finalQualData('handlePass'),
                "HANDLEDAMAGE"  : self.flatT('handleDamage'),
                "RECOVID"       : self.flatT('recovID'),
                "RECOVPASS"     : self.finalQualData('recovPass'),
                "RECOVMETH"     : self.flatT('recovMeth'),
                "SPECUSEID"     : self.flatT('specUseID'),
                "SPECUSEPASS"   : self.finalQualData('specUsePass'),
                "SPECUSEDESCR"  : self.flatT('specUseDescr'),
                "QATC_OK"       : self._QATC,
                "QACCE_OK"      : self._QACCE,
                "FINALSTAGE"    : self._Destination,
                "COMMENT"       : self._Notes,
                "SOFTVERSION"   : DESIGN
              }
        }

        return outJSON

        
#____________________________
class HM():
    def __init__(self,SN,code):
        self._SN   = SN
        self._code = code

    @classmethod
    def fromJD(cls,jD):
        SN   = jD["SN"  ]
        code = jD["code"]
        return cls(SN,code)

    def toJD(self):
        outJD = { "SN" : self._SN, "code" : self._code }
        return outJD

    def SN(self):
        return self._SN
    def code(self):
        return self._code

#____________________________
class QAmini():
    def __init__(self,SN,code):
        self._SN   = SN
        self._code = code

    @classmethod
    def fromJD(cls,jD):
        SN   = jD["SN"  ]
        code = jD["code"]
        return cls(SN,code)

    def toJD(self):
        outJD = { "SN" : self._SN, "code" : self._code }
        return outJD

    def SN(self):
        return self._SN
    def code(self):
        return self._code

#____________________________
class QAchip():
    def __init__(self,SN,code):
        self._SN   = SN
        self._code = code

    @classmethod
    def fromJD(cls,jD):
        SN   = jD["SN"  ]
        code = jD["code"]
        return cls(SN,code)

    def toJD(self):
        outJD = { "SN" : self._SN, "code" : self._code }
        return outJD

    def SN(self):
        return self._SN
    def code(self):
        return self._code

#____________________________
