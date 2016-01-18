Search.setIndex({envversion:46,filenames:["api/data_api","api/functions","api/graphgen_api","api/info_api","api/json_api","api/nifti_api","api/ocp_types","api/overlay_api","api/propagate_api","api/public_api","api/ramon_api","api/stats_api","api/swc_api","api/tile_api","index","sphinx/config","sphinx/console","sphinx/datamodel","sphinx/faq","sphinx/ingesting","sphinx/introduction"],objects:{"":{"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/xy/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:z_slice)/(int:time_slice)/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-xy-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-z_slice)-(int-time_slice)-"],"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/xz/(int:resolution)/(int:min_x),(int:max_x)/(int:y_slice)/(int:min_z),(int:max_z)/(int:time_slice/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-xz-(int-resolution)-(int-min_x),(int-max_x)-(int-y_slice)-(int-min_z),(int-max_z)-(int-time_slice-"],"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/yz/(int:resolution)/(int:x_slice)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:time_slice)/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-yz-(int-resolution)-(int-x_slice)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/(int:annotation_id)/(string:option_args)/(int:resolution)/":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-(int-annotation_id)-(string-option_args)-(int-resolution)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/(string:graph_type)/(int:Xmin)/(int:Xmax)/(int:Ymin)/(int:Ymax)/(int:Zmin)/(int:Zmax)/":[2,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-(string-graph_type)-(int-Xmin)-(int-Xmax)-(int-Ymin)-(int-Ymax)-(int-Zmin)-(int-Zmax)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/(string:option_args)/":[10,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-(string-option_args)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/blosc/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:min_time),(int:max_time)/":[0,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-blosc-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-min_time),(int-max_time)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/getField/(string:ramon_field)/":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-getField-(string-ramon_field)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/getPropagate/":[12,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-getPropagate-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/hdf5/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:min_time),(int:max_time)/":[0,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-hdf5-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-min_time),(int-max_time)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/jpeg/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-jpeg-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/merge/(string:listofids)/(string:option_args)/":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-merge-(string-listofids)-(string-option_args)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/npz/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:min_time),(int:max_time)/":[0,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-npz-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-min_time),(int-max_time)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/setField/(string:ramon_field)/(string/int/float:ramon_value)":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-setField-(string-ramon_field)-(string-int-float-ramon_value)"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/setPropagate/(int:propagate_value)/":[8,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-setPropagate-(int-propagate_value)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/xy/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:z_slice)/(int:time_slice)/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-xy-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-z_slice)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/xz/(int:resolution)/(int:min_x),(int:max_x)/(int:y_slice)/(int:min_z),(int:max_z)/(int:time_slice/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-xz-(int-resolution)-(int-min_x),(int-max_x)-(int-y_slice)-(int-min_z),(int-max_z)-(int-time_slice-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/yz/(int:resolution)/(int:x_slice)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:time_slice)/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-yz-(int-resolution)-(int-x_slice)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/createChannel/":[4,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-createChannel-"],"(string:server_name)/ocp/ca/(string:token_name)/deleteChannel/":[4,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-deleteChannel-"],"(string:server_name)/ocp/ca/(string:token_name)/info/":[3,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-info-"],"(string:server_name)/ocp/ca/(string:token_name)/projinfo/":[3,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-projinfo-"],"(string:server_name)/ocp/ca/autoIngest/":[4,1,1,"post-(string-server_name)-ocp-ca-autoIngest-"],"(string:server_name)/ocp/ca/public_tokens/":[9,0,1,"get-(string-server_name)-ocp-ca-public_tokens-"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/all/":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-all-"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/genHist/":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-genHist-"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/hist/":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-hist-"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/mean/":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-mean-"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/percentile/(decimal:percentile_value)":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-percentile-(decimal-percentile_value)"],"(string:server_name)/ocp/stats/(string:token_name)/(string:channel_name)/std/":[11,0,1,"get-(string-server_name)-ocp-stats-(string-token_name)-(string-channel_name)-std-"],Exceptions:[19,3,1,""],Scaling:[19,3,1,""],ocpca:[1,2,0,"-"]},"(string:server_name)/ocp/catmaid/(string:token_name)/(string:channel_name)/(string:slice_type)/(int:time)/(int:zvalue)/(int:ytile)_(int:xtile)_(int:resolution)":{png:[13,0,1,"get-(string-server_name)-ocp-catmaid-(string-token_name)-(string-channel_name)-(string-slice_type)-(int-time)-(int-zvalue)-(int-ytile)_(int-xtile)_(int-resolution).png"]},"(string:server_name)/ocp/catmaid/mcfc/(string:token_name)/(string:channel_name):(string:color_name)/(string:slice_type)/(int:time)/(int:zvalue)/(int:ytile)_(int:xtile)_(int:resolution)":{png:[13,0,1,"get-(string-server_name)-ocp-catmaid-mcfc-(string-token_name)-(string-channel_name)-(string-color_name)-(string-slice_type)-(int-time)-(int-zvalue)-(int-ytile)_(int-xtile)_(int-resolution).png"]},"(string:server_name)/ocp/catmaid/viking/(string:token_name)/volume/(string:channel_name)/(int:resolution)/X(int:xtile)_Y(int:xtile)_Z(int:zvalue)":{png:[13,0,1,"get-(string-server_name)-ocp-catmaid-viking-(string-token_name)-volume-(string-channel_name)-(int-resolution)-X(int-xtile)_Y(int-xtile)_Z(int-zvalue).png"]}},objnames:{"0":["http","get","HTTP get"],"1":["http","post","HTTP post"],"2":["py","module","Python module"],"3":["py","function","Python function"]},objtypes:{"0":"http:get","1":"http:post","2":"py:module","3":"py:function"},terms:{"0_0_3":13,"17psi6gfyjpexqmwl":[],"1_1_4":13,"1st":11,"2100x2000":17,"2x2":17,"50th":11,"512x512":13,"99th":11,"case":[0,2,3,4,5,7,8,9,10,12,13,19],"default":[0,5,7,8,10,12,13,17,19],"final":17,"float":[6,7,10,17],"import":19,"int":[0,2,7,8,10,13,17,19],"new":[16,17,18],"return":[2,8,11],"true":[17,19],"try":[17,19],"while":8,abl:17,about:[14,17],abov:[6,16,17,19],accept:19,access:[],account:16,acm:14,acquaint:17,across:[8,18],activ:18,actual:17,add:[16,19],addition:11,address:19,administr:[],adminstr:18,advantag:17,after:[17,19],again:17,aid:[],algorithm:[14,20],align:17,all:[3,9,11,14,17,18,19,20],allow:[6,8,11,17,19],alpha_valu:7,alphanumer:[17,19],alreadi:[16,18],also:[9,13,17,18],although:17,analysi:[14,17,20],analyz:17,anaylsi:0,ani:19,anisotropi:17,annnot:6,annot:[],annotation_id:10,anoth:[16,17],answer:18,anyon:17,appli:18,applic:[3,4,9,13],appropri:16,arbitrari:11,architectur:[14,20],archiv:18,argument:[10,11],arrai:[0,14,20],ask:[],assign:[17,19],associ:[3,6,17],assum:17,authent:19,auto:19,avail:[14,20],avali:9,avoid:[14,20],axon:14,background:8,bad:11,base:[11,17,19],basic:[11,17],becom:[16,17],been:18,befor:[17,18,19],begin:18,below:[8,16,19],berger:14,between:[2,17],bibtex:14,big:8,bit:6,blob:19,bock11:9,bock:14,both:[8,11],bound:0,box:[16,18],brain:[14,20],branch:18,browser:0,bug:18,build:[14,20],burn:14,calcul:11,call:[8,17,19],can:[0,6,8,9,10,11,13,15,16,17,18,19],cannot:8,canon:0,captur:17,cassandra:15,cassndara:[],catmaid:[13,19],caus:16,celeri:15,center:14,certain:6,chan1:4,chan2:4,chan3:4,chang:16,channel:[],channel_nam:[0,2,4,5,8,10,11,12,13],channel_typ:[3,4],channeltyp:[0,7],chatroom:14,check:8,checkout:18,checout:18,choic:17,chung:14,cite:14,clarif:[],clariti:14,click:16,client:20,clone:18,cluster:[14,20],cmyrgb:13,code:[0,2,3,4,5,7,8,9,10,11,12,13,18,19],coeffici:17,collect:[17,19],color:[6,13],color_nam:13,com:19,comma:10,comment:19,commit:[17,19],common:18,commonli:18,complex:17,compon:[17,19],compos:17,compress:0,comput:[11,14,20],configur:[],connect:[14,19,20],consid:17,consist:[8,17],consol:[],constraint:11,contact:[],contain:[3,17,19],content:[0,3,4,9,13],contradict:[17,19],contribut:18,control:[17,19],convent:17,coordin:17,correspond:[10,17,19],cortex1:19,cortex:[14,19],cortic:19,could:17,count:17,creat:[],cube_dimens:3,current:[11,17,19],cut:10,databas:[10,11,13,14,17,20],datamodel:[],dataset:[],dataspac:17,datatyp:[0,3,4,6,7,11,17],dataurl:19,datset:0,debug:[],decim:11,defin:17,deisseroth:14,delet:4,dendrit:14,deploi:18,deriv:14,describ:[0,14],descript:3,design:[14,20],desir:16,detail:[10,16,17],detect:[14,20],dev:18,develop:18,deviat:[],dictionari:[],differ:[6,8,14,17,19,20],diffus:17,digit:19,dimenison:6,dimens:[2,6,17],direct:[2,14,16,20],directli:[11,18],directori:19,discuss:18,disk:[14,20],displai:17,distribut:[14,20],doc:[],document:[10,14,17],doe:[8,17],doesn:11,done:[8,11],doubl:[],down:[16,17],download:[0,19],downsampl:8,drop:16,dropbox:19,dti:17,due:11,each:[2,3,6,13,16,17,19],edit:[16,19],edu:[1,19],effect:[14,17,20],effici:17,effort:17,either:18,electron:[14,20],enabl:[17,19],encount:19,end:[2,11],engin:17,entit:6,entri:[],enumer:[17,19],error:[0,2,3,4,5,7,8,9,10,11,12,13],etc:[11,17],evalu:[14,20],event:19,ex10r55:9,ex12r75:9,ex12r76:9,ex13r51:9,ex14r58:9,examin:17,exampl:[0,3,4,6,9,13,17,19],exampleserv:19,excel:18,except:[3,10,17,19],excess:17,execut:[14,20],exist:[],experi:17,explan:[],expos:11,express:11,extend:18,extra:19,fail:19,fals:[17,19],faq:[],featur:18,few:11,figur:19,file:[0,2,3,4,5,7,8,9,10,12,13,19],fill:16,first:[7,17,19],first_channel_nam:7,first_server_nam:7,first_token_nam:7,float32:[0,6,7,11,17],fly:11,fmri:17,folder:19,follow:[6,16,17,18,19],form:[0,4,7,19],format:[0,2,3,4,5,7,8,9,10,12,13,19],forum:18,found:[0,2,3,4,5,7,8,9,10,11,12,13,16,18],fraction:17,frequent:[],from:[0,5,9,10,11,12,13,14,17,19,20],full:16,further:14,furthermor:11,gener:[0,2,3,4,5,7,8,9,10,11,12,13,17,18,19],generatejson:19,genhist:11,getpropag:[],gigabyt:11,git:18,github:[14,18,19],gitter:14,give:17,given:17,glm:17,googl:[],googlegroup:[],got:17,grai:14,graph:[2,5,12],graph_typ:2,grayscal:13,grosenick:14,group:[0,7],happen:17,hard:19,have:[6,8,14,16,17,18,19],head:18,help:18,her:17,here:[16,18,19],hierarchi:19,high:[14,20],highest:17,highlight:[14,20],hist:11,histogram:[],histolog:14,hold:19,host:[0,3,4,7,9,13,17],host_server_nam:7,how:[],howev:[17,19],http:[0,3,4,9,13,16,19],idea:18,idenitfi:8,identifi:18,illustr:19,image1:17,images:3,imagetypeiterationnumb:17,imagin:17,implement:18,improv:[14,20],includ:[3,14,17,19,20],index:[14,20],individu:6,infrastructur:11,ingest:[],inherit:[14,20],initi:[17,19],input:[16,17],insid:[6,19],instal:[15,18],integ:[6,11],intens:[14,20],interfac:[11,14,20],interfer:[14,20],intern:18,introduct:[],isotrop:[17,19],issu:18,jhu:1,kashturi11:17,kasthuri11:[0,3,9,13,17],kasthuri:14,kazhdan:14,kei:[],kind:[17,19],kleissa:14,know:[14,17],knowledg:17,kunal:1,label:19,labnamepublicationyear:17,larg:17,leadresearchercurrentyear:17,learn:[17,18],left:14,let:[14,17],level:17,librari:0,lichtman:14,lillanei:[1,14],line:16,linear:17,link:17,list:[4,9,10,14,18],listofid:10,load:0,locat:19,lock:8,log:16,login:16,look:[4,10,18],mai:18,mail:[14,18],main:16,maintain:[8,19],major:[2,19],make:[8,17,18],manavalan:14,mani:17,map:[6,14,17,20],master:[18,19],materi:19,max:11,max_i:[0,7],max_tim:[0,7],max_x:[0,7],max_z:[0,7],maxim:[14,20],maximum:[0,7,17],mcfc:13,mean:[],membran:14,memori:11,mention:6,menu:16,metadata:[3,4,6,17],method:17,microscopi:[14,20],might:[17,18],min:11,min_i:[0,7],min_tim:[0,7],min_x:[0,7],min_z:[0,7],minimum:[0,7,17],miss:[0,5,7,8,10,12,13],mni152:17,modal:17,model:[],modifi:16,more:[10,17,19],most:[2,17],mous:[14,19],mri:[14,17],much:[14,17,20],mulitpl:18,multi:[14,17,20],multimod:14,multipl:[0,6,17],must:[11,17,19],mydata:19,mysql:15,name:[0,2,3,4,5,7,8,9,10,11,12,13,16,17,19],namesubprojectnam:17,navig:[16,18],ndio:18,neariso_scaledown:3,need:19,neural:[14,20],neurodata:[],neurodataviz:18,neuron:2,neurosci:14,neuroscientist:17,nginx:15,node:[2,14,20],none:[17,19],normal:19,nosql:[14,20],note:[11,14,17],now:[16,17],npz:0,number:[17,19],object:[],ocp:[],ocptilecach:13,offset:[3,17],onc:[16,19],onli:[0,7,8,11,13,17,19],openconnecto:[0,2,3,4,5,7,8,9,10,11,12,13,16,19],openconnectom:19,oper:19,option:[0,2,5,7,8,10,12,13,16,17,18,19],option_arg:10,options_arg:10,organ:[14,19,20],orient:[17,19],origin:17,other:[17,18,19],our:[11,17,18],out:[14,20],output:14,over:[17,18],overarch:[17,19],overwrit:10,own:17,page:[16,17,18],paint:6,pair:17,parallel:[14,20],paramet:[0,2,3,4,5,7,8,9,10,11,12,13,16,17],part:18,particular:17,partit:[14,20],patient:8,per:17,percent:11,percentile_valu:11,perform:[14,20],perlman:14,permiss:17,person:17,pixel:17,place:18,plane:[0,17,19],pleas:[1,8,14,18],pli:[],png:[13,19],point:[3,6,17,18,19],portion:19,prefer:16,prefix:19,present:17,preserv:10,primarili:[14,17,20],prior:18,privat:17,probabl:[6,14],problem:17,probmap:[0,7],product:[14,20],program:[14,20],projinfo:3,propag:[],propagate_valu:8,properti:6,propgat:8,propos:18,provid:[11,14,17,18,20],public_token:9,publicli:[9,14,17,19,20],pull:18,put:[9,17,18,19],python2:19,python:[0,19],quantiti:6,question:[],queu:11,quit:8,rabbitmq:15,ramon:[],ramon_field:10,ramon_valu:10,rang:[11,17],rather:11,read:[11,14,17,19,20],readabl:17,readonli:[3,4],ref:[],refer:[3,8,18,19],reflect:[18,19],region:0,regist:[14,16,17],reid:14,relationship:17,releas:14,relev:17,repo:[14,18],report:18,repositori:18,repres:[2,6,17],reproduc:17,request:[0,3,4,9,11,13,18],requir:[17,19],research:17,resolut:[0,3,7,8,10,13,17],respons:[0,3,4,9,13],rest:[11,14,17,20],retriev:11,rgb32:[0,7],rgb64:[0,7],rgba:6,riak:15,right:[14,16],righthand:18,roncal:14,root:19,run:[18,19,20],sai:17,same:[6,17,19],sampl:17,save:19,scalabl:[14,17,20],scale:[3,14,17,19,20],scalinglevel:3,scan:17,scienc:[14,20],script:[15,19],search:[17,18],second:[7,17,19],second_channel_nam:7,second_server_nam:7,second_token_nam:7,section:19,see:[16,18],select:[16,18],separ:[10,17],seri:[14,17,19,20],server:[0,2,3,4,5,7,8,9,10,11,12,13,15,17,18,19],server_nam:[0,2,3,4,5,8,9,10,11,12,13],set:[6,8,10,11,14,15,17,19,20],sheet:4,should:[16,17,18,19],side:18,sign:16,signfi:8,similarli:[13,17],simpl:[14,17,20],simpler:17,simpli:19,sinc:11,singl:0,size:17,slice_typ:13,slot:19,smith:14,solid:[14,20],somatosensori:14,some:[8,16,18,19],someth:8,space:17,spatial:[14,20],specif:[8,17,19],specifi:[0,3,10,11,17,19],spreadsheet:[],ssdbm:14,standard:[],start:[2,11,17,18],state:[8,14,17,20],stateless:[14,20],statu:[0,2,3,4,5,7,8,9,10,11,12,13,17],std:11,storag:[14,17,20],store:[6,11,14,17,19],string:[0,2,3,4,5,7,8,9,10,11,12,13],sub:[16,19],subject1:17,subject1t1:17,subject:17,success:4,suffici:17,suffix:19,suggest:[17,18,19],support:[2,6,11,14,17,18,19],sure:19,synaps:[2,20],synopsi:[0,2,3,4,5,7,8,9,10,11,12,13],syntax:[0,2,3,4,5,7,8,9,10,11,12,13],system:[14,20],szalai:14,tabl:[8,17],tag:18,take:[8,17],takemura13:9,taken:[16,17],tar:14,tech:4,terabyt:11,term:[],test:18,test_kat1:4,than:19,thei:17,themselv:19,thi:[0,2,3,4,5,7,8,9,10,11,12,13,17,18,19],thought:17,three:[],through:[17,19],throughput:[14,20],thy1eyfpbrain10:13,tif:19,tiff:[0,17,19],tilecach:13,time0:19,time1:19,time2:19,time:[6,13,14,17,18,19,20],time_slic:[0,7],timen:19,timerang:[0,3,7],timeseri:[0,6,7,13,17],timestepstart:17,timestepstop:17,timseri:6,todo:15,togeth:17,token:[],token_nam:[0,2,3,4,5,8,10,11,12,13],tomographi:14,tool:18,touch:18,tupl:17,tutori:16,two:[10,19],type:[],typic:[11,17],ualex:15,uint16:[0,6,7,11,17],uint32:[0,6,7,17],uint64:[6,17],uint8:[0,3,4,6,7,11,17],under:[8,18],understand:17,uniqu:6,unit:17,univers:19,unus:16,unweight:2,upload:[],uploaddata:19,upsampl:8,url:19,usabl:[14,20],user:[11,17,18,19],valu:[0,6,7,8,10,13,17,19],variabl:[],variou:11,version:3,vertic:2,via:8,view:[13,16,17,18],viewabl:[17,19],vike:13,vision:[14,20],visit:[17,18],vist:17,visual:[17,19,20],vogelstein:14,volum:13,voxel:17,voxelr:3,wai:17,want:17,warn:[8,16],web:[11,14,18,20],weiler:14,well:[3,11,17,19],were:17,what:[17,18],when:[8,19],where:[16,17],which:[6,8,11,13,14,16,17,18,19,20],window:17,windowrang:3,wish:[16,17,18],within:[0,17],wnnu8kophuyuarx2yqb3iwkgvi:[],work:[13,17],workflow:20,workload:[14,20],worth:19,would:[17,19],write:[14,17,20],written:17,x1_y1_z10:13,x_slice:[0,7],xmax:2,xmin:2,xrang:[0,7],xtile:13,xyz:6,y_slice:[0,7],yet:[16,18],ymax:2,ymin:2,you:[0,6,8,13,14,15,16,17,18,19],your:[0,6,8,16,17,18,19],yrang:[0,7],ytile:13,z_slice:[0,7],zenodo:14,zip:14,zmax:2,zmin:2,zoom:17,zrang:[0,7],zslice:[3,13],zvalu:13},titles:["Data APIs","open-connectome Functions","GrahpGen APIs","Project Info APIs","JSON APIs","NIFTI APIs","NeuroData Types","Overlay APIs","Propagate APIs","Public Token APIs","RAMON APIs","Statistics API","SWC APIs","Tile APIs","Open Connectome","Configuration","Administrator Console","Data Model","Frequently Asked Questions (FAQ)","How to Ingest Data","Introduction"],titleterms:{"function":1,"public":9,access:16,addit:19,administr:16,allstatist:11,annot:10,api:[0,2,3,4,5,7,8,9,10,11,12,13],ask:18,assumpt:17,attribut:17,autoingest:4,blosc:0,channel:[6,16,17],combin:6,configur:15,connectom:1,consol:16,contact:14,creat:16,createchannel:4,cutout:[0,7],cutut:7,data:[0,6,17,19],dataset:[16,17],deletechannel:4,deviat:11,exist:16,explan:19,faq:18,field:10,frequent:18,genhistogram:11,get:[0,3,7,9,10],getfield:10,getgraph:2,gethistogram:11,getmcfctil:13,getnifti:5,getpropag:8,getsimpletil:13,getswc:12,getvikingtil:13,grahpgen:2,guid:[],hdf5:[0,3],histogram:11,how:[16,19],imag:[0,19],info:3,inform:3,informatio:3,ingest:19,introduct:20,jpeg:0,json:[3,4],knosso:0,mean:11,merg:10,model:17,neurodata:[6,14],nifti:5,numpi:0,object:10,ocp:[],open:1,overlai:7,overview:[17,19],percentil:11,possibl:6,post:[0,10],prep:19,project:[3,16,17],propag:8,queri:10,question:18,quick:[],ramon:10,servic:[0,3,7,8,10,11],setfield:10,setpropag:8,slice:[0,7],stack:0,standard:11,stat:11,statist:11,swc:12,term:19,tile:13,token:[9,16,17],type:[6,19],unsupport:19,updat:16,upload:19}})