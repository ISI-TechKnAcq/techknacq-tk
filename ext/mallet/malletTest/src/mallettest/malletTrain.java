/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package mallettest;

import cc.mallet.classify.Classifier;
import cc.mallet.pipe.iterator.CsvIterator;
import cc.mallet.types.Labeling;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author Marcial
 */
public class malletTrain {
    
    Classifier clasificador=null;
    private File tempFile;
    static final String directorioClasificador="src/clasificador";
    
    
    public boolean loadClassifier(){
        boolean banderaClasificadorOk=false;
        File dirClasificadores = new File(directorioClasificador);
        File[] listadoDeClasificadores = dirClasificadores.listFiles();
        if (listadoDeClasificadores != null) {
                        for (File clasificadorActual : listadoDeClasificadores) {
                
                if (!clasificadorActual.getName().equals(".DS_Store")){
                    System.out.println(clasificadorActual.getName());
                    try {
                        this.loadClassifier(clasificadorActual);
                        banderaClasificadorOk=true;
                    } catch (IOException | ClassNotFoundException ex) {
                        Logger.getLogger(MalletTest.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
        }
    }
        
    return banderaClasificadorOk;
   }    
    
    public void loadClassifier(File serializedFile)
        throws FileNotFoundException, IOException, ClassNotFoundException {

        // The standard way to save classifiers and Mallet data                                            
        //  for repeated use is through Java serialization.                                                
        // Here we load a serialized classifier from a file.                                               

        Classifier classifier;

        try (ObjectInputStream ois = new ObjectInputStream (new FileInputStream (serializedFile))) {
            classifier = (Classifier) ois.readObject();
        }
        
        this.clasificador=classifier;
        System.out.println("clasificador '"+serializedFile.getName()+"' ha sido cargado con exito");

        //return classifier;
    }
    
        public void creaArchivoTemporal(String nombre) throws IOException{
        this.tempFile = File.createTempFile(nombre, ".temp");
        // Delete temp file when program exits.
        this.tempFile.deleteOnExit();
        }

    
        public void printLabelings(File file) throws IOException {

        // Create a new iterator that will read raw instance data from                                     
        //  the lines of a file.                                                                           
        // Lines should be formatted as:                                                                   
        //                                                                                                 
        //   [name] [label] [data ... ]                                                                    
        //                                                                                                 
        //  in this case, "label" is ignored.                                                              

        CsvIterator reader =
            new CsvIterator(new FileReader(file),
                            "(\\w+)\\s+(\\w+)\\s+(.*)",
                            3, 2, 1);  // (data, label, name) field indices               

        // Create an iterator that will pass each instance through                                         
        //  the same pipe that was used to create the training data                                        
        //  for the classifier.                                                                            
        Iterator instances =
            this.clasificador.getInstancePipe().newIteratorFrom(reader);

        // Classifier.classify() returns a Classification object                                           
        //  that includes the instance, the classifier, and the                                            
        //  classification results (the labeling). Here we only                                            
        //  care about the Labeling.                                                                       
        while (instances.hasNext()) {
            Labeling labeling = this.clasificador.classify(instances.next()).getLabeling();

            // print the labels with their weights in descending order (ie best first)                     

            for (int rank = 0; rank < labeling.numLocations(); rank++){
                System.out.print(labeling.getLabelAtRank(rank) + ":" +
                                 labeling.getValueAtRank(rank) + " ");
            }
            System.out.println();

        }
    }
    
    public void printDatoSingle(String id, String contenidoCampo) throws IOException {
           //x es el campo, en este caso es ignorado ya que clasifica segun los tipos que 
           //trae el clasificador de entrada
           String singleData=id+" x "+contenidoCampo;
        try (FileWriter fWriter = new FileWriter(this.tempFile,true)) {
            fWriter.write(singleData);
            fWriter.flush();
        }
        
        // Create a new iterator that will read raw instance data from                                     
        //  the lines of a file.                                                                           
        // Lines should be formatted as:                                                                   
        //                                                                                                 
        //   [name] [label] [data ... ]                                                                    
        //                                                                                                 
        //  in this case, "label" is ignored. 

        CsvIterator reader =
            new CsvIterator(new FileReader(tempFile),
                            "(\\w+)\\s+(\\w+)\\s+(.*)",
                            3, 2, 1);  // (data, label, name) field indices               

        // Create an iterator that will pass each instance through                                         
        //  the same pipe that was used to create the training data                                        
        //  for the classifier.                                                                            
        Iterator instances =
            this.clasificador.getInstancePipe(). newIteratorFrom(reader);

        // Classifier.classify() returns a Classification object                                           
        //  that includes the instance, the classifier, and the                                            
        //  classification results (the labeling). Here we only                                            
        //  care about the Labeling.                                                                       
        while (instances.hasNext()) {
            Labeling labeling = this.clasificador.classify(instances.next()).getLabeling();

            // print the labels with their weights in descending order (ie best first)                     
            
            //El campo x es agregado como un nuevo tipo de campo, pero este no es util
            //Por ello se ignora restando 1 a la cantidad de labels que posee la clasificacion
            for (int rank = 0; rank < labeling.numLocations()-1; rank++){
                System.out.print(labeling.getLabelAtRank(rank) + ":" +
                                 labeling.getValueAtRank(rank) + " ");
                
            }
            System.out.println();

        }
    }
    
    public Map<String, String> obtieneClasificacionSingle(String id, String contenidoCampo) throws IOException {
           //x es el campo, en este caso es ignorado ya que clasifica segun los tipos que 
           //trae el clasificador de entrada
            //
           Map<String, String> clasificacionSingle = new HashMap<>();
           String singleData;
        singleData = id+" x "+contenidoCampo;
        try (FileWriter fWriter = new FileWriter(this.tempFile,true)) {
            fWriter.write(singleData);
            fWriter.flush();
        }
        
        // Create a new iterator that will read raw instance data from                                     
        //  the lines of a file.                                                                           
        // Lines should be formatted as:                                                                   
        //                                                                                                 
        //   [name] [label] [data ... ]                                                                    
        //                                                                                                 
        //  in this case, "label" is ignored. 

        CsvIterator reader =
            new CsvIterator(new FileReader(tempFile),
                            "(\\w+)\\s+(\\w+)\\s+(.*)",
                            3, 2, 1);  // (data, label, name) field indices               

        // Create an iterator that will pass each instance through                                         
        //  the same pipe that was used to create the training data                                        
        //  for the classifier.                                                                            
        Iterator instances =
            this.clasificador.getInstancePipe(). newIteratorFrom(reader);

        // Classifier.classify() returns a Classification object                                           
        //  that includes the instance, the classifier, and the                                            
        //  classification results (the labeling). Here we only                                            
        //  care about the Labeling.                                                                       
        while (instances.hasNext()) {
            Labeling labeling = this.clasificador.classify(instances.next()).getLabeling();

            // print the labels with their weights in descending order (ie best first)                     
            
            //El campo x es agregado como un nuevo tipo de campo, pero este no es util
            //Por ello se ignora

            for (int rank = 0; rank < labeling.numLocations(); rank++){
                if (!"x".equals(labeling.getLabelAtRank(rank)+"")){
                    clasificacionSingle.put(labeling.getLabelAtRank(rank)+"", labeling.getValueAtRank(rank)+"");
                }
            }
        }
        return clasificacionSingle;
    }
    
}
