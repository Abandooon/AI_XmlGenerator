// src/validation/semantic_check/DroolsValidator.java
import org.kie.api.KieServices;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;

public class DroolsValidator {
    public static void main(String[] args) {
        KieServices ks = KieServices.Factory.get();
        KieContainer kContainer = ks.getKieClasspathContainer();
        KieSession kSession = kContainer.newKieSession("autosarValidation");

        String xml = args[0];
        kSession.insert(xml);
        int errorCount = kSession.fireAllRules();

        System.exit(errorCount > 0 ? 1 : 0);
    }
}