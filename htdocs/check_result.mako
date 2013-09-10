<!DOCTYPE html>
<html>
<head>

    <script src="/static/jquery.min.1.9.1.js"></script>
    <title></title>
</head>
    <script language="JavaScript">
        function exists() {
            return true;
        }
        $(document).ready(function() {
            window.parent.verifyData('${cmp}');
         });
    </script>
<body>
</body>
</html>