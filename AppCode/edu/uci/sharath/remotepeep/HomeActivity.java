package edu.uci.sharath.remotepeep;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.Drawable;
import android.os.AsyncTask;
import android.support.v7.app.ActionBarActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.parse.*;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class HomeActivity extends ActionBarActivity {

    ImageView imageDisp;
    TextView timeDisp;

    List<ParseObject> allImages;
    int totalImages=0;
    int currImage = 0;
    boolean isStarted = false;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        // parse setup
        Parse.initialize(this, "g6riYDc21ziBVBHWXxLbMot7KVBMg1kdFm9xqU27", "W19zTrzotKyrH6vld8tzHwhKipZB8X6qNRrHyNwp");
        ParseInstallation.getCurrentInstallation().saveInBackground();
        ParsePush.subscribeInBackground("R-Peep", new SaveCallback() {
            @Override
            public void done(ParseException e) {
                if (e == null) {
                    isStarted = true;
                    Log.d("com.parse.push", "successfully subscribed to the broadcast channel.");
                } else {
                    Log.e("com.parse.push", "failed to subscribe for push", e);
                }
            }
        });
        allImages = new ArrayList<ParseObject>();
        imageDisp = (ImageView) findViewById(R.id.imageId);
        timeDisp = (TextView) findViewById(R.id.timeId);

        getListofImages();
    }

    @Override
    protected void onResume(){
        super.onResume();
        if(isStarted)
            getListofImages();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_home, menu);
        //getMenuInflater().inflate(R.menu., menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }else if (id == R.id.openDoorId) {
            sendNotification(1);
            return true;
        }else if(id == R.id.alarmId){
            sendNotification(2);
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    private void getListofImages(){
        ParseQuery<ParseObject> query = ParseQuery.getQuery("Images");
        query.orderByDescending("createdAt");
        query.setLimit(10);
        query.findInBackground(new FindCallback<ParseObject>() {
            public void done(List<ParseObject> list, ParseException e) {
                if (e == null) {
                    allImages = list;
                    Log.d("score", "Retrieved " + allImages.size() + " scores");
                    if (allImages != null)
                        totalImages = allImages.size();
                    if (totalImages > 0) {
                        currImage = 0;
                        displayImage(allImages.get(currImage));
                    } else {
                        timeDisp.setText("");
                        new DownloadImageTask(imageDisp).execute("http://ecx.images-amazon.com/images/I/51f8-lERVzL._SY355_.jpg");
                    }
                } else {
                    Log.d("score", "Error: " + e.getMessage());
                }
            }
        });
    }

    private void displayImage(ParseObject img){
        timeDisp.setText(img.getCreatedAt().toString());
        new DownloadImageTask(imageDisp).execute(img.getParseFile("picture").getUrl());
    }
    public void onLatestClick(View v){
        sendNotification(0);
    }

    public void sendNotification(int type){
        final int cmd = type;
        ParseQuery<ParseObject> query = ParseQuery.getQuery("Commands");
        query.getInBackground("RUBrwMGFil", new GetCallback<ParseObject>() {
            public void done(ParseObject command, ParseException e) {
                if (e == null) {
                    command.put("alarm", 0);
                    command.put("camera", 0);
                    command.put("door", 0);
                    if (cmd == 0)
                        command.put("camera", 1);
                    else if (cmd == 1)
                        command.put("door", 1);
                    else if (cmd == 2)
                        command.put("alarm", 1);
                    command.saveInBackground();
                    Toast.makeText(HomeActivity.this, "Your Request Sent", Toast.LENGTH_SHORT).show();
                }
            }
        });

    }

    public void prev(View v){
        if(currImage<totalImages-1){
            currImage++;
            displayImage(allImages.get(currImage));
        }else
            Toast.makeText(this, "No more visitors", Toast.LENGTH_SHORT).show();

    }
    public void next(View v){
        if(currImage>0){
            currImage--;
            displayImage(allImages.get(currImage));
        }else
            Toast.makeText(this, "No more visitors", Toast.LENGTH_SHORT).show();
    }

    private class DownloadImageTask extends AsyncTask<String, Void, Bitmap> {
        ImageView bmImage;

        public DownloadImageTask(ImageView bmImage) {
            this.bmImage = bmImage;
        }

        protected Bitmap doInBackground(String... urls) {
            String urldisplay = urls[0];
            Bitmap visitorPic = null;
            try {
                InputStream in = new java.net.URL(urldisplay).openStream();
                visitorPic = BitmapFactory.decodeStream(in);
            } catch (Exception e) {
                Log.e("Error", e.getMessage());
            }
            return visitorPic;
        }

        protected void onPostExecute(Bitmap result) {
            bmImage.setImageBitmap(result);
        }
    }
}
