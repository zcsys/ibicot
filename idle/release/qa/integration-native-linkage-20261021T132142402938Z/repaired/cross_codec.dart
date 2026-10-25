import 'dart:convert';
import 'promoted/game/platform/lib/study_recorder.dart';
class Memory implements StudyStore {
 Memory(this.value); String? value;
 Future<String?> read() async => value;
 Future<bool> compareAndSwap(String? expected,String next) async {value=next;return true;}
}
Future<void> main() async {
  for(final v in [1,1.0,2,2.0,true]) {
    final raw={'schema_version':v,'registry':null,'records':[],'status':'withdrawn'};
    try { await StudyRecorder.open(Memory(studyCanonical(raw))); print('erased schema=$v(${v.runtimeType}) accepted'); }
    catch(e){print('erased schema=$v(${v.runtimeType}) rejected');}
  }
  for(final field in ['application_id','application_version','application_build']) {
    final raw=<String,dynamic>{'version':1,'status':'available','source':'native_process_observation_v1','native_pid':123,'platform':'ios','application_id':'dev.tideglass.game','application_version':'1.0','application_build':'1','observed_start_utc_ms':100000};
    raw[field]='${raw[field]}\n';
    try {StudyProcessObservation.fromJson(raw);print('$field final newline accepted');}
    catch(e){print('$field final newline rejected');}
  }
}
