var mysql = require('mysql');

var con = mysql.createConnection({
    host: 'jeevan.ckiej05nbavj.us-east-1.rds.amazonaws.com', 
    user: 'jeevan', 
    password: 'jeevan2020',
    database: "twitterdata"
});

exports.negativeTweets = function(event, context, callback){
    console.log(event);
    var sql = "select tweets.original_author, tweets.text, negativeScore from sentiments inner join tweets on tweets.id = sentiments.id and tweets.created_at = sentiments.created_at order by negativeScore desc limit 10";
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
