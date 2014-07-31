# Descriptions exists here:
# https://portal.nordu.net/display/SWAMID/Entity+Categories#EntityCategories
# -SFS1993%3A1153

NREN_DESC = (
    "<b>National research and education network</b>(NREN)<br>"
    "The application is provided by the Swedish NREN (SUNET) which is "
    "ultimately responsible for its operation."
    "This category is only relevant for attribute-release between SWAMID "
    "registered IdPs and SUNET services.<br /><br />This category "
    "should return the attribute: <ul><li>eduPersonTargetedID</li></ul>")

RE_DESC = (
    "<b>Research & Education</b>(RE)<br />"
    "The Research & Education category applies to low-risk services that "
    "support research and education as an essential component. For instance, a "
    "service that provides tools for both multi-institutional research "
    "collaboration and instruction is eligible as a candidate for this "
    "category. This category is very similar to InCommons Research & "
    "Scolarship Category. The recommended IdP behavior is to release name, "
    "eppn, eptid, mail and eduPersonScopedAffiliation which also aligns with "
    "the InCommon recommendation only if the services is also in at least one "
    "of the safe data processing categories. It is also a recommendation that "
    "static organisational information is released."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>givenName</li><li>initials</li>"
    "<li>displayName</li><li>c</li><li>o</li><li>ou</li>"
    "<li>eduPersonPrincipalName</li><li>sn</li>"
    "<li>eduPersonScopedAffiliation</li><li>email</li></ul>")

SFS_DESC = (
    "<b>Svensk f&ouml;rfattningssamling 1993:1153</b>(SFS)<br />"
    "The SFS 1993:1153 category applies to services that fulfill "
    "<a href='http://www.riksdagen.se/sv/Dokument-Lagar/Lagar/"
    "Svenskforfattningssamling/Forordning-19931153-om-redo_sfs-1993-1153' "
    "target='_blank'>SFS 1993:1153</a>. SFS 1993:1153 limits membership in "
    "this category to services provided by Swedish HEI-institutions, VHS.se or "
    "SCB.se. Example services include common government-operated student- and "
    "admissions administration services such as LADOK and NyA aswell as "
    "enrollment and course registration services. Inclusion in this category "
    "is strictly reserved for applications that are governed by SFS 1993:1153 "
    "which implies that the application may make use of norEduPersonNIN. The "
    "recommended IdP behavior is to release norEduPersonNIN."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>norEduPersonNIN</li></ul>")

EU_DESC = (
    "<b>EU Adequate Protection</b>(EU)<br />"
    "The application is compliant with any of the EU adequate protection for "
    "3rd countries according to EU Commission decisions on the adequacy of the "
    "protection of personal data in third countries. This category includes "
    "for instance applications that declares compliance with US safe-harbor."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li></ul>")

HEI_DESC = (
    "<b>HEI Service</b>(HEI)<br />"
    "The application is provided by a Swedish HEI which is ultimately "
    "responsible for its operation."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li></ul>")

RS_DESC = (
    "<b>Research & Scholarship</b>(RS)<br />"
    "Candidates for the Research and Scholarship (R&S) "
    "Category are Service Providers that support research "
    "and scholarship interaction, collaboration or management "
    "as an essential component."
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>givenName</li>"
    "<li>displayName</li><li>eduPersonPrincipalName</li>"
    "<li>sn</li><li>eduPersonScopedAffiliation</li><li>mail</li></ul>")

COC_DESC = (
    "<b>Code of Conduct</b>(CoC)<br />The GEANT Data protection Code of "
    "Conduct (CoC) defines an approach on European level to "
    "meet the requirements of the EU data protection directive for releasing "
    "mostly harmless personal attributes to a Service Provider (SP) from an "
    "Identity Provider (IdP). "
    "For more information please see GEANT Data Protection Code of Conduct. "
    "<br /><br />This category should return the attributes:"
    "<ul><li>eduPersonTargetedID</li><li>eduPersonPrincipalName</li>"
    "<li>eduPersonScopedAffiliation</li><li>email</li><li>givenName</li>"
    "<li>sn</li><li>displayName</li><li>schachomeorganization</li></ul>")