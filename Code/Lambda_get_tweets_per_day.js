var mysql = require('mysql');

var con = mysql.createConnection({
    host: 'jeevan.ckiej05nbavj.us-east-1.rds.amazonaws.com', 
    user: 'jeevan', 
    password: 'jeevan2020',
    database: "twitterdata"
});

exports.findData = function(event, context, callback){
    console.log(event);
    var sql = "select str_to_date(concat(substring(created_at, 5,6),' ', substring(created_at, -4,4)),'%b %e %Y') as Date, count(*) as tweets_count from tweets group by Date order by Date desc limit 1";
    con.query(sql, function (error, result, fields) {
    	if (error) throw error;
        var response = {
          "statusCode": 200,
          "body": JSON.stringify(result)
        };
        console.log(response);
        context.succeed(response);
        return;
    });
};
