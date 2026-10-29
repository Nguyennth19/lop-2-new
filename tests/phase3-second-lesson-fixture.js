/* Phase 3 engineering fixture — NOT book-aligned or approved curriculum.
   Run with node tests/phase3-second-lesson-fixture.js after exporting the
   generic renderer logic into a test harness (or use the checks below). */
(function(global) {
 const lesson={
  status:'success',schemaVersion:'1.0',lessonId:'MATH_B021_QA_ONLY',
  lesson:{lesson_id:'MATH_B021_QA_ONLY',title:'Bài QA kỹ thuật (không phải SGK)',status:'TEST_ONLY'},
  sections:[
   {section_id:'B021_QA_S1',lesson_id:'MATH_B021_QA_ONLY',level:1,title:'QA đặt tính',exercise_type:'VERTICAL_ADD',sort_order:1},
   {section_id:'B021_QA_S2',lesson_id:'MATH_B021_QA_ONLY',level:1,title:'QA tính nhẩm',exercise_type:'MENTAL_ADD',sort_order:2},
   {section_id:'B021_QA_S3',lesson_id:'MATH_B021_QA_ONLY',level:2,title:'QA lời văn',exercise_type:'WORD_PROBLEM',sort_order:3},
   {section_id:'B021_QA_S4',lesson_id:'MATH_B021_QA_ONLY',level:3,title:'QA tìm chữ số',exercise_type:'MISSING_DIGIT',sort_order:4}
  ],
  questions:[
   {question_id:'B021_QA_Q1',section_id:'B021_QA_S1',question_type:'VERTICAL_ADD',sort_order:1,payload:{n1:28,n2:15,op:'+',answer:43}},
   {question_id:'B021_QA_Q2',section_id:'B021_QA_S2',question_type:'MENTAL_ADD',sort_order:1,payload:{n1:26,n2:4,op:'+',answer:30}},
   {question_id:'B021_QA_Q3',section_id:'B021_QA_S3',question_type:'WORD_PROBLEM',sort_order:1,payload:{desc:'Có 12 viên bi, thêm 19 viên bi. Hỏi có tất cả bao nhiêu viên bi?',summary:'12 viên; thêm 19 viên',solution:'Có tất cả số viên bi là:',n1:12,n2:19,op:'+',answer:31,unit:'viên bi'}},
   {question_id:'B021_QA_Q4',section_id:'B021_QA_S4',question_type:'MISSING_DIGIT',sort_order:1,payload:{rows:[['2',{ans:8}],[{ans:1},'5'],['4','3']],sum:43,answer:43,op:'+'}}
  ],
  content:[],sources:[],assets:[]
 };
 if(typeof module!=='undefined' && module.exports)module.exports=lesson;
 else global.PHASE3_TEST_LESSON=lesson;
})(typeof window!=='undefined'?window:this);
