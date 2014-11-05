<!DOCTYPE html>
<html>
<head>

    <script src="/static/jquery.min.1.9.1.js"></script>
    <title></title>
</head>
    <script language="JavaScript">
        var $j = jQuery.noConflict();

        function exists() {
            return true;
        }
        $j(document).ready(function() {
            window.parent.verifyData('${cmp}');
         });
    </script>
<body>
</body>
</html>