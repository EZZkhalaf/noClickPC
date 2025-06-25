import React , { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View , TouchableOpacity, TextInput, Button} from 'react-native';
import { Alert } from 'react-native';


const   App = () => {
  const [fatcat , setFatcat] = useState('');

  


  const fetchServer = async() =>{
    try {
      const response = await fetch('http://192.168.0.119:5000/submit' , {
        method:'POST',
        headers : {
          'Content-Type' : 'application/json'
        },
        body:JSON.stringify({
          text:fatcat
        })
      });
      const result = await response.json();
      Alert.alert('Python says:', result.message);
    } catch (error) {
        console.log("Network error:", err.message);
        Alert.alert('Network error', err.message);
    }
  }

  return (
    <View style={styles.container}>

        <TextInput 
          style={styles.textArea }
          placeholder='control'
          multiline
          numberOfLines={4}
          onChangeText={(e)=>setFatcat(e)}
        />
        <Button style={styles.button}  title='send' onPress={fetchServer}/>
    </View>
  );
}


const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center', // Vertical centering
    alignItems: 'center',     // Horizontal centering
    backgroundColor: '#f5f5f5',
  },
  textArea: {
    height: 150,
    width: '80%',
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    backgroundColor: 'white',
    textAlignVertical: 'top', // Aligns text at the top of the TextArea
  },
  button:{
    borderColor: 'black',
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    
    backgroundColor: 'white'
  }
});

export default App;