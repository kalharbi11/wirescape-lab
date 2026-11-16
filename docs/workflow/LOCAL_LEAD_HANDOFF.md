<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Local lead checkpoint — 2026-11-16

Sole active delivery lead: gpt-lead, LOCAL chat01a1e5ad-ea43-7b12-bc15-85ff572f1843.
Existing wlab-lead-review ACTIVE every45minutes. One lead/timer; Claude-lead stepped down.
Local device-results branch and untracked captures preserved. Read liveCURRENT first, then AGENTS,
CODEX_LEAD/contracts/latestbatch82. This checkpoint replaces older queue snapshots.

## Owner decisions and Fable
User explicitly requested CLAUDE.md autonomy change:128merged2b632ee. Fable chooses useful runscope,
questioncount, reading/delegation and stoppingpoint. Creating aPRdoesnotendthe session.
Fable does NO PRreviews/reviewmonitoring. Lead reviews delegatedwork. IfcontractrequiresClaude-specific
review, tellownerwhoassignsClaudeReviewer. Fable retains design rulings and milestone acceptance.
No newClaudeBuilderwork aftercurrenttasksfinish;111S2stillownerstart/staffingdecision.

## Completed and acceptance
Claude-lead merges verifiedlive:12349747bd(authaggregates/tokenaudit0matches),1199f883a1(Q12),
602c4d3d0(R2),116e0d4437(E1a),12657f866b(role),127042454d(CURRENT).
Earlier1067bf71ae/124aa16185done. Q13ruling131mergedc6cd8fc.
118final5cffcacfixedtwoinvalidsourcecites, exactnotesCI43966331470success, merged3dd68f2.
AllM0buildertasksnowmerged. Acceptance issue132 needs/fable maps eachtasktoPR/fullhead/merge/evidence.
Fable decides acceptance; T0.14owneropen, ringmod2unmeasured, continuityrawcapturesnotuploaded,
physicaldevice-onlygaps, baselineIDcountlowerbound andadvisoryhostedtiming are explicit exceptions.
Do not claim M0 accepted or silently waive exceptions. B4finished118/stopped; no newtaskassigned.

## Active writers and review
- B1 #125/PR130 task/125-studio-apply-graph f4da1145665bd8c9b33b10413c85d52e8f9dc900.
  All14Lab43964958640jobsPASS, but root/Worker2source review3High/1Medium. Finalremaininground2/2
  countingpreviousselfcorrection posted6930813610 andsentexistingB1. Fixgen-onlyACKsettlement
  falselyconfirmingunapplied; overlappingapplyGraphfallingbacktoloadGraphwhileawaitingACK;
  JSON.stringifyconfigorderrejectingvalidunapplied; FakeEnginereplacednotesource/alwaysreplacedOSCOutparity.
  Onecohesiveapps/studio-onlypush+regressions/fullCI/signedResult; no broaderPV3redesign.
  No furtherordinaryroundafterthis; preciseQUESTIONifarchitecture/outofscope/unresolved.
- B2 #109/PR129 task/109-sanitizer-ccache21bc87c405be6813cdbc9bb382c9058d3f4b35c8.
  Singleci.ymlwriter, sanitizersjobonly. Contentcheck correction present, no test/flag/aggregate changes.
  Base/priorhead82orderedabi2CTestnames equal; currentheadinventory stillneedsverification.
  Historical20runs91rows:71validmedian3s/max387s,10skips+10negativeattemptintervalsexcluded.
  ColdPR346s/49of274hits/cachemiss is NOTwarm evidence. K8requiresactualmatchedwarm<=318s.
  EarlierassumptionthatmanualcacheonthissamefeaturebranchisinvisibletoPR was wrong: officialGitHub
  docs allowcurrentfeaturebranchcache access. K7alreadypermitsmanualcold/no restore/save.
  LeadlaunchedONEcoldmanual43966200132, exact21bc87c verified; sanitizerjob133646255526
  wasrunninglastinspection. After actualcoldsuccess+SAVEkey/compilerflags/ccachestats proof,
  leadFULLrerunsPR43964380415 and verifiesactualmatchingwarmrestore/duration. No bootstrapmerge,
  PRcachesave, settingschange or prematureclosefromcoldtiming. B2keepsbranchstable/noextratriggers.
  Temporarybackgroundwatcher wasREJECTEDbyauto-review, no processstarted; existingleadheartbeat
  performsnextstatecheck. No modelpoll/sleep loop or duplicate timer.
- B3 #86/PR105 task/86-pv1-protocol-v0 priorheade98456154692e041c40c4a74e6645421d1f723a4.
  Q13 accepted131/3ffb55c andmergedc6cd8fc. FINALround3/3formallydispatched86/105andsentB3.
  maxbus_channel15/boundary0,15,16,63,-1,nonintegerparityPythonTSCPPsidecar,explain63source;
  D08facts-onlyDesktoprejectsspacevsQ8/sidecaraccept, noDesktop/Q8edits. CheckactualIDgenerators
  forpossible0x20; ifonecanemitit,reportlivebugseparately. AddapplyGraphschema/capability/replycorpus
  orrecorddisagreementpersecondmergeobligation. Unknownfieldskept/generatorsunwired/noboundsweep.
  IfpacketfailsreviewNO4thdispatch:revertfailingitemtoitspriorstateandrecorddisagreementperQ13,
  stillrequireexactheadcorpus/drift/fullrequiredCI/acceptance4; no redwaiver.
- Claude1/3finishedSTOPPED. Claude2#111noPRfound, ownerdecidescurrentS2start/S3staffing.

## Routing
RegularChatGPTChat only, neverWork/Codex: B1 6afadca6-071c-83ea-a029-b22c1560a794;
B2 6afadc8d-5138-83ea-bb36-88048b6bf54d; B3 6afadc7c-9b44-83ea-be32-dbd465646ce0;
B4 6afadc5f-8478-83ea-89a0-6b2bedf3b2a9.
Worker2durable6afad0f1-55a8-8191-975f-f008479ba02f read-onlysupport.130reviewcomplete/sourcefindings
rootverified; don'trepeatunchangedreview. Promptdelivery/activeflagaloneisnotexecution; inspectactualResults.

## Invariants and hygiene
Fullrerunalljobsforfailedaggregate, neverfailed-only. Onecohesivepushperround, twoordinaryroundsmax
thenQUESTIONS exceptauthorizedQ13third. No devices/MIDI/LAN/forcepush/gateweakening/settings/credits.
Keepbyteidenticaldepseedingrecipe,CMakeconfigureafter session.cpp/S0copy,OSCOutreplacementfact.
Everyrunreconcileopenissue/PR owner/head/branch/status/blocker/nextaction; closeansweredduplicates
withevidence,mergeacceptedgreenworkpromptly, updateprimarydescriptions/CURRENT/batch82/timer.
No branchdeletionorunfinishedage-onlyclosure. Preserve20percentfivehourreserve; actualresetverified0percent
thisrun, no resetcreditsused. UseindependentworkwhileCIruns, no modelwaiting/pollingloops.

Signed: gpt-lead, 2026-11-16
